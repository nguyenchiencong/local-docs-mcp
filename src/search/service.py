"""
Decoupled Semantic Search Service

This service provides semantic search capabilities independent of the indexing process.
It connects to Qdrant and Ollama for search operations only.
"""

import functools
import math
from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue, SearchParams
import ollama

from .models import SearchResult, SearchConfig


class SemanticSearchService:
    """
    Decoupled semantic search service that provides various search strategies
    without depending on the indexing process.
    """

    def __init__(self, config: SearchConfig):
        self.config = config
        self._client = None
        self._embedding_cache = {}  # Cache for frequently used queries

    @functools.cache
    def get_qdrant_client(self) -> QdrantClient:
        """Get cached Qdrant client"""
        if self._client is None:
            self._client = QdrantClient(url=self.config.qdrant_url, prefer_grpc=True)
        return self._client

    def _get_search_params(self) -> SearchParams:
        """Build reusable Qdrant search params"""
        return SearchParams(hnsw_ef=self.config.search_hnsw_ef)

    def _embed_query(self, query: str) -> List[float]:
        """Embed a single query with caching for efficiency"""
        if query is None:
            query = ""

        normalized_query = query.strip()

        if not normalized_query:
            # Return a stable zero vector for empty queries to avoid downstream errors
            return [0.0] * self.config.embedding_dimension

        # Check cache first
        if normalized_query in self._embedding_cache:
            return self._embedding_cache[normalized_query]

        # Use direct HTTP request to Ollama for better performance
        try:
            import requests

            response = requests.post(
                f"{self.config.embedding_url}/api/embeddings",
                json={
                    "model": self.config.embedding_model,
                    "prompt": normalized_query
                },
                timeout=5  # Short timeout for search responsiveness
            )
            response.raise_for_status()
            embedding = response.json()["embedding"]

            # Cache the result (limit cache size to prevent memory issues)
            if len(self._embedding_cache) < 100:
                self._embedding_cache[normalized_query] = embedding

            return embedding
        except Exception as e:
            # Fallback to ollama library if direct request fails
            print(f"Warning: Direct embedding request failed, using ollama library: {e}")
            response = ollama.embed(
                model=self.config.embedding_model,
                input=normalized_query
            )
            return response.embeddings[0]

    def _convert_to_search_results(self, qdrant_results: List) -> List[SearchResult]:
        """Convert Qdrant results to SearchResult objects"""
        results = []
        for result in qdrant_results:
            results.append(SearchResult(
                id=result.payload.get("id", ""),
                filename=result.payload.get("filename", ""),
                text=result.payload.get("text", ""),
                score=result.score,
                embedding=result.vector if hasattr(result, 'vector') else [],
                location=result.payload.get("location", 0),
                token_count=result.payload.get("token_count"),
                start_index=result.payload.get("start_index"),
                end_index=result.payload.get("end_index")
            ))
        return results

    def semantic_search(
        self,
        query: str,
        limit: Optional[int] = None,
        min_similarity_score: Optional[float] = None
    ) -> List[SearchResult]:
        """
        Perform semantic search on indexed documents.

        Args:
            query: Search query string
            limit: Maximum number of results to return
            min_similarity_score: Minimum similarity score threshold

        Returns:
            List of search results ranked by similarity
        """
        limit = limit or self.config.default_limit
        min_score = min_similarity_score or self.config.default_similarity_threshold

        # Get query embedding
        query_embedding = self._embed_query(query)

        # Search in Qdrant
        client = self.get_qdrant_client()
        search_results = client.query_points(
            collection_name=self.config.qdrant_collection,
            query=query_embedding,
            using="text_embedding",
            limit=limit * 2,  # Get more results initially for filtering
            score_threshold=min_score,
            search_params=self._get_search_params(),
        ).points

        # Convert and filter results
        results = self._convert_to_search_results(search_results)

        # Apply additional filtering if needed
        if min_score > self.config.default_similarity_threshold:
            results = [r for r in results if r.score >= min_score]

        return results[:limit]

    def hybrid_search(
        self,
        query: str,
        semantic_weight: Optional[float] = None,
        limit: Optional[int] = None,
        min_similarity_score: Optional[float] = None,
        keyword_boost_factor: float = 1.5
    ) -> List[SearchResult]:
        """
        Combine semantic search with keyword matching.

        Args:
            query: Search query string
            semantic_weight: Weight for semantic search (0-1, where 1 is pure semantic)
            limit: Maximum number of results to return
            min_similarity_score: Minimum similarity score threshold
            keyword_boost_factor: Boost factor for exact keyword matches

        Returns:
            List of hybrid search results
        """
        limit = limit or self.config.default_limit
        min_score = min_similarity_score or self.config.default_similarity_threshold
        semantic_weight = (
            semantic_weight
            if semantic_weight is not None
            else self.config.hybrid_semantic_weight
        )

        # Stage 1: Semantic search
        semantic_results = self.semantic_search(
            query,
            limit=limit * 2,  # Get more candidates for re-ranking
            min_similarity_score=min_score
        )

        if not semantic_results:
            return []

        # Stage 2: Keyword matching on semantic results
        query_terms = self._extract_search_terms(query)
        keyword_scores = self._calculate_keyword_scores(
            semantic_results, query_terms, query.lower()
        )

        # Stage 3: Score fusion
        final_results = []
        for result in semantic_results:
            keyword_score = keyword_scores.get(result.id, 0.0)

            # Apply boost for exact matches
            if keyword_score > 0.8:  # High keyword match
                keyword_score *= keyword_boost_factor

            # Normalize and combine scores
            normalized_semantic = result.score
            normalized_keyword = min(keyword_score, 1.0)

            final_score = (
                semantic_weight * normalized_semantic +
                (1 - semantic_weight) * normalized_keyword
            )

            # Create new result with combined score
            combined_result = SearchResult(
                id=result.id,
                filename=result.filename,
                text=result.text,
                score=final_score,
                embedding=result.embedding,
                location=result.location,
                token_count=result.token_count,
                start_index=result.start_index,
                end_index=result.end_index
            )
            final_results.append(combined_result)

        # Sort by final score and return top results
        final_results.sort(key=lambda x: x.score, reverse=True)
        return self._rerank_with_mmr(final_results, limit)

    def document_retrieval(self, document_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve full document by ID.

        Args:
            document_id: Unique identifier for the document

        Returns:
            Document metadata and content if found, None otherwise
        """
        client = self.get_qdrant_client()

        # Search for the specific document ID
        search_results = client.scroll(
            collection_name=self.config.qdrant_collection,
            scroll_filter=Filter(
                must=[
                    FieldCondition(
                        key="id",
                        match=MatchValue(value=document_id)
                    )
                ]
            ),
            limit=1
        )

        if not search_results[0]:  # No results found
            return None

        point = search_results[0][0]
        return {
            "id": point.payload.get("id"),
            "filename": point.payload.get("filename"),
            "text": point.payload.get("text"),
            "location": point.payload.get("location"),
            "token_count": point.payload.get("token_count"),
            "start_index": point.payload.get("start_index"),
            "end_index": point.payload.get("end_index"),
            "embedding": point.vector if hasattr(point, 'vector') else []
        }

    def search_with_metadata_filter(
        self,
        query: str,
        metadata_filter: Dict[str, Any],
        limit: Optional[int] = None,
        min_similarity_score: Optional[float] = None
    ) -> List[SearchResult]:
        """
        Search with metadata constraints.

        Args:
            query: Search query string
            metadata_filter: Dictionary of metadata fields to filter by
            limit: Maximum number of results to return
            min_similarity_score: Minimum similarity score threshold

        Returns:
            List of filtered search results
        """
        limit = limit or self.config.default_limit
        min_score = min_similarity_score or self.config.default_similarity_threshold

        # Get query embedding
        query_embedding = self._embed_query(query)

        # Build Qdrant filter from metadata
        filter_conditions = []
        for key, value in metadata_filter.items():
            if isinstance(value, dict):
                # Handle range filters, date ranges, etc.
                if "start" in value and "end" in value:
                    # This would need to be implemented based on your specific metadata structure
                    pass
            else:
                # Simple equality filter
                filter_conditions.append(
                    FieldCondition(
                        key=key,
                        match=MatchValue(value=value)
                    )
                )

        # Search in Qdrant with metadata filter
        client = self.get_qdrant_client()
        search_filter = Filter(must=filter_conditions) if filter_conditions else None

        search_results = client.query_points(
            collection_name=self.config.qdrant_collection,
            query=query_embedding,
            using="text_embedding",
            query_filter=search_filter,
            limit=limit,
            score_threshold=min_score,
            search_params=self._get_search_params(),
        ).points

        return self._convert_to_search_results(search_results)

    def _cosine_similarity(self, vec_a: List[float], vec_b: List[float]) -> float:
        """Compute cosine similarity between two vectors"""
        if not vec_a or not vec_b:
            return 0.0

        length = min(len(vec_a), len(vec_b))
        if length == 0:
            return 0.0

        dot_product = 0.0
        norm_a = 0.0
        norm_b = 0.0
        for i in range(length):
            a = vec_a[i]
            b = vec_b[i]
            dot_product += a * b
            norm_a += a * a
            norm_b += b * b

        if norm_a == 0 or norm_b == 0:
            return 0.0

        return dot_product / (math.sqrt(norm_a) * math.sqrt(norm_b))

    def _rerank_with_mmr(
        self,
        results: List[SearchResult],
        limit: int,
        lambda_param: Optional[float] = None
    ) -> List[SearchResult]:
        """
        Apply a lightweight MMR re-ranking step to promote diversity in results.
        """
        if lambda_param is None:
            lambda_param = self.config.mmr_lambda

        if len(results) <= 1:
            return results[:limit]

        selected: List[SearchResult] = []
        candidates = list(results)

        while candidates and len(selected) < limit:
            best_candidate = None
            best_score = float("-inf")

            for candidate in candidates:
                diversity_penalty = 0.0
                if selected and candidate.embedding:
                    similarities = [
                        self._cosine_similarity(candidate.embedding, chosen.embedding)
                        for chosen in selected
                        if chosen.embedding
                    ]
                    if similarities:
                        diversity_penalty = max(similarities)

                mmr_score = lambda_param * candidate.score - (1 - lambda_param) * diversity_penalty

                if mmr_score > best_score:
                    best_score = mmr_score
                    best_candidate = candidate

            if best_candidate is None:
                break

            selected.append(best_candidate)
            candidates.remove(best_candidate)

        if len(selected) < limit:
            # If we ran out of candidates due to missing embeddings, fall back to remaining order
            selected.extend(candidates[: limit - len(selected)])

        return selected[:limit]

    def _extract_search_terms(self, query: str) -> List[str]:
        """
        Extract meaningful search terms from query.

        Args:
            query: The search query string

        Returns:
            List of processed search terms
        """
        import re

        # Extract word tokens, remove punctuation, convert to lowercase
        terms = re.findall(r'\b\w+\b', query.lower())

        # Filter out very short terms and common stopwords
        # Simple stopword list - could be enhanced with a proper library
        simple_stopwords = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'up', 'about', 'into', 'through', 'during',
            'before', 'after', 'above', 'below', 'between', 'among', 'is', 'are',
            'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do',
            'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might',
            'can', 'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she',
            'it', 'we', 'they', 'what', 'which', 'who', 'when', 'where', 'why',
            'how', 'not', 'no', 'yes', 'if', 'then', 'else', 'there', 'here'
        }

        filtered_terms = []
        for term in terms:
            if len(term) > 2 and term not in simple_stopwords:
                filtered_terms.append(term)

        return filtered_terms

    def _calculate_keyword_scores(
        self,
        results: List[SearchResult],
        query_terms: List[str],
        raw_query: Optional[str] = None
    ) -> Dict[str, float]:
        """
        Calculate keyword matching scores for each result.

        Args:
            results: List of search results to score
            query_terms: List of extracted search terms
            raw_query: Original search query (lowercased)

        Returns:
            Dictionary mapping result IDs to keyword scores
        """
        scores = {}

        if not query_terms:
            return scores

        normalized_query = (raw_query or "").strip().lower()

        for result in results:
            text_lower = result.text.lower()
            filename_lower = (result.filename or "").lower()
            score = 0.0
            term_count = len(query_terms)

            # Count exact term matches
            matches = 0
            for term in query_terms:
                if term in text_lower:
                    matches += 1

                    # Bonus for multiple occurrences of the same term
                    term_occurrences = text_lower.count(term)

                    # Bonus for term density (capped to prevent spam)
                    occurrence_bonus = min(term_occurrences / 10, 0.3)
                    score += occurrence_bonus

            # Boost when the entire query phrase shows up in the chunk
            if normalized_query and normalized_query in text_lower:
                score += 0.3

            # Modest boost for filename matches
            if filename_lower:
                filename_hits = sum(1 for term in query_terms if term in filename_lower)
                if filename_hits:
                    score += min(filename_hits / term_count, 0.2)

            # Base score from term coverage (what percentage of query terms were found)
            base_score = matches / term_count

            # Final keyword score combines coverage and occurrence bonuses
            final_score = base_score + score

            # Ensure score doesn't exceed 1.0 for normalization purposes
            scores[result.id] = min(final_score, 1.0)

        return scores

    def get_collection_info(self) -> Dict[str, Any]:
        """Get information about the Qdrant collection"""
        client = self.get_qdrant_client()
        try:
            collection_info = client.get_collection(self.config.qdrant_collection)
            return {
                "name": self.config.qdrant_collection,
                "vectors_count": getattr(collection_info, 'vectors_count', 0),
                "indexed_vectors_count": getattr(collection_info, 'indexed_vectors_count', 0),
                "points_count": getattr(collection_info, 'points_count', 0),
                "status": getattr(collection_info.status, 'value', 'unknown') if hasattr(collection_info, 'status') else 'unknown',
                "optimizer_status": getattr(collection_info.optimizer_status, 'value', 'unknown') if hasattr(collection_info, 'optimizer_status') else 'unknown',
                "vector_size": getattr(collection_info.config.params.vectors, 'size', 0) if hasattr(collection_info, 'config') and hasattr(collection_info.config, 'params') and hasattr(collection_info.config.params, 'vectors') else 0
            }
        except Exception as e:
            return {"error": str(e)}
