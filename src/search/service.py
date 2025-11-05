"""
Decoupled Semantic Search Service

This service provides semantic search capabilities independent of the indexing process.
It connects to Qdrant and Ollama for search operations only.
"""

import functools
from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue
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

    def _embed_query(self, query: str) -> List[float]:
        """Embed a single query with caching for efficiency"""
        # Check cache first
        if query in self._embedding_cache:
            return self._embedding_cache[query]

        # Use direct HTTP request to Ollama for better performance
        try:
            import requests

            response = requests.post(
                f"{self.config.embedding_url}/api/embeddings",
                json={
                    "model": self.config.embedding_model,
                    "prompt": query
                },
                timeout=5  # Short timeout for search responsiveness
            )
            response.raise_for_status()
            embedding = response.json()["embedding"]

            # Cache the result (limit cache size to prevent memory issues)
            if len(self._embedding_cache) < 100:
                self._embedding_cache[query] = embedding

            return embedding
        except Exception as e:
            # Fallback to ollama library if direct request fails
            print(f"Warning: Direct embedding request failed, using ollama library: {e}")
            response = ollama.embed(
                model=self.config.embedding_model,
                input=query
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
            score_threshold=min_score
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
        semantic_weight: float = 0.7,
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
        keyword_scores = self._calculate_keyword_scores(semantic_results, query_terms)

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
        return final_results[:limit]

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
            score_threshold=min_score
        ).points

        return self._convert_to_search_results(search_results)

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

    def _calculate_keyword_scores(self, results: List[SearchResult], query_terms: List[str]) -> Dict[str, float]:
        """
        Calculate keyword matching scores for each result.

        Args:
            results: List of search results to score
            query_terms: List of extracted search terms

        Returns:
            Dictionary mapping result IDs to keyword scores
        """
        scores = {}

        if not query_terms:
            return scores

        for result in results:
            text_lower = result.text.lower()
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

                    # Bonus for exact phrase matches (if the term appears as part of the original query)
                    # This handles cases where users search for multi-word phrases

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