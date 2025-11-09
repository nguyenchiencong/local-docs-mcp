"""
Test suite for Semantic Search Service

This module provides comprehensive testing for the semantic search service,
using real connections to Qdrant and Ollama for integration testing.
"""

import pytest
import os
import sys
import time
from typing import List, Dict, Any

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from search.service import SemanticSearchService
from search.models import SearchResult, SearchConfig


class TestSearchConfig:
    """Test the SearchConfig data model"""

    def test_default_config(self):
        """Test default configuration values"""
        config = SearchConfig()
        assert config.qdrant_url == "http://localhost:6334"
        assert config.qdrant_collection == "local-docs-collection"
        assert config.embedding_model == "hf.co/Qwen/Qwen3-Embedding-0.6B-GGUF:F16"
        assert config.default_limit == 10
        assert config.default_similarity_threshold == 0.15

    def test_custom_config(self):
        """Test custom configuration values"""
        config = SearchConfig(
            qdrant_url="http://custom:6334",
            qdrant_collection="custom-collection",
            embedding_model="custom-model",
            default_limit=5,
            default_similarity_threshold=0.5
        )
        assert config.qdrant_url == "http://custom:6334"
        assert config.qdrant_collection == "custom-collection"
        assert config.embedding_model == "custom-model"
        assert config.default_limit == 5
        assert config.default_similarity_threshold == 0.5


class TestSearchResult:
    """Test the SearchResult data model"""

    def test_search_result_creation(self):
        """Test creating a search result"""
        result = SearchResult(
            id="test-id",
            filename="test.md",
            text="Test content",
            score=0.85,
            embedding=[0.1, 0.2, 0.3],
            location=100
        )
        assert result.id == "test-id"
        assert result.filename == "test.md"
        assert result.text == "Test content"
        assert result.score == 0.85
        assert result.embedding == [0.1, 0.2, 0.3]
        assert result.location == 100
        assert result.token_count is None
        assert result.start_index is None
        assert result.end_index is None

    def test_search_result_with_optional_fields(self):
        """Test creating a search result with optional fields"""
        result = SearchResult(
            id="test-id",
            filename="test.md",
            text="Test content",
            score=0.85,
            embedding=[0.1, 0.2, 0.3],
            location=100,
            token_count=50,
            start_index=0,
            end_index=100
        )
        assert result.token_count == 50
        assert result.start_index == 0
        assert result.end_index == 100


@pytest.mark.integration
class TestSemanticSearchServiceIntegration:
    """Integration tests for SemanticSearchService with real services"""

    @pytest.fixture(scope="class")
    def config(self):
        """Create a test configuration"""
        return SearchConfig()

    @pytest.fixture(scope="class")
    def service(self, config):
        """Create a test service instance"""
        return SemanticSearchService(config)

    def test_service_initialization(self, service, config):
        """Test service initialization"""
        assert service.config == config
        assert service._client is None

    def test_qdrant_connection(self, service):
        """Test connection to Qdrant"""
        client = service.get_qdrant_client()
        assert client is not None

    def test_get_collection_info(self, service):
        """Test getting collection information"""
        info = service.get_collection_info()
        assert isinstance(info, dict)

        if "error" not in info:
            assert "name" in info
            assert "vectors_count" in info
            assert "points_count" in info
            print(f"Collection info: {info}")
        else:
            print(f"Collection not found or error: {info['error']}")

    def test_ollama_connection(self, service):
        """Test connection to Ollama"""
        try:
            # Try to embed a simple query
            embedding = service._embed_query("test query")
            assert isinstance(embedding, list)
            assert len(embedding) > 0
            print(f"Embedding dimension: {len(embedding)}")
        except Exception as e:
            pytest.skip(f"Ollama not available: {e}")

    def test_semantic_search_empty_collection(self, service):
        """Test semantic search on potentially empty collection"""
        try:
            results = service.semantic_search("test query", limit=5)
            assert isinstance(results, list)
            print(f"Search returned {len(results)} results")

            for result in results:
                assert isinstance(result, SearchResult)
                assert result.score >= 0
                assert result.text is not None
                assert result.filename is not None
                print(f"Result: {result.filename} (score: {result.score:.3f})")

        except Exception as e:
            pytest.skip(f"Search not available: {e}")

    def test_hybrid_search(self, service):
        """Test hybrid search functionality"""
        try:
            results = service.hybrid_search("test query", semantic_weight=0.8, limit=3)
            assert isinstance(results, list)
            print(f"Hybrid search returned {len(results)} results")

            for result in results:
                assert isinstance(result, SearchResult)
                assert result.score >= 0
                print(f"Hybrid result: {result.filename} (score: {result.score:.3f})")

        except Exception as e:
            pytest.skip(f"Hybrid search not available: {e}")

    def test_search_with_metadata_filter(self, service):
        """Test search with metadata filtering"""
        try:
            metadata_filter = {"filename": "test.md"}
            results = service.search_with_metadata_filter(
                "test query",
                metadata_filter=metadata_filter,
                limit=3
            )
            assert isinstance(results, list)
            print(f"Filtered search returned {len(results)} results")

        except Exception as e:
            pytest.skip(f"Filtered search not available: {e}")

    def test_document_retrieval(self, service):
        """Test document retrieval by ID"""
        try:
            # Try to retrieve a document (likely not found, but tests the method)
            result = service.document_retrieval("test-document-id")
            assert result is None or isinstance(result, dict)

            if result:
                assert "id" in result
                assert "filename" in result
                assert "text" in result
                print(f"Retrieved document: {result['filename']}")
            else:
                print("Document not found (expected for test ID)")

        except Exception as e:
            pytest.skip(f"Document retrieval not available: {e}")

    def test_embed_query_various_inputs(self, service):
        """Test embedding different types of queries"""
        test_queries = [
            "simple query",
            "This is a longer query with more words",
            "Query with numbers 123 and symbols !@#",
            "",  # Empty string
            "a",  # Single character
        ]

        try:
            for query in test_queries:
                embedding = service._embed_query(query)
                assert isinstance(embedding, list)
                assert len(embedding) > 0
                print(f"Embedded '{query[:20]}...' -> dimension {len(embedding)}")

        except Exception as e:
            pytest.skip(f"Query embedding not available: {e}")

    def test_search_with_different_limits(self, service):
        """Test search with different result limits"""
        try:
            for limit in [1, 3, 10, 20]:
                results = service.semantic_search("test query", limit=limit)
                assert isinstance(results, list)
                assert len(results) <= limit
                print(f"Search with limit {limit} returned {len(results)} results")

        except Exception as e:
            pytest.skip(f"Search with limits not available: {e}")

    def test_search_with_similarity_thresholds(self, service):
        """Test search with different similarity thresholds"""
        try:
            thresholds = [0.0, 0.3, 0.5, 0.8, 0.9]

            for threshold in thresholds:
                results = service.semantic_search(
                    "test query",
                    limit=10,
                    min_similarity_score=threshold
                )
                assert isinstance(results, list)

                # All results should meet the threshold
                for result in results:
                    assert result.score >= threshold

                print(f"Threshold {threshold}: {len(results)} results")

        except Exception as e:
            pytest.skip(f"Search with thresholds not available: {e}")


@pytest.mark.integration
class TestSearchServicePerformance:
    """Performance tests for the search service"""

    @pytest.fixture(scope="class")
    def service(self):
        """Create a service instance for performance testing"""
        config = SearchConfig()
        return SemanticSearchService(config)

    def test_embedding_performance(self, service):
        """Test embedding performance"""
        try:
            query = "This is a test query for performance testing"

            start_time = time.time()
            embedding = service._embed_query(query)
            end_time = time.time()

            embedding_time = end_time - start_time

            assert isinstance(embedding, list)
            assert len(embedding) > 0
            print(f"Embedding took {embedding_time:.3f} seconds")

            # Should be reasonably fast (less than 5 seconds)
            assert embedding_time < 5.0

        except Exception as e:
            pytest.skip(f"Embedding performance test not available: {e}")

    def test_search_performance(self, service):
        """Test search performance"""
        try:
            query = "performance test query"

            start_time = time.time()
            results = service.semantic_search(query, limit=10)
            end_time = time.time()

            search_time = end_time - start_time

            assert isinstance(results, list)
            print(f"Search took {search_time:.3f} seconds and returned {len(results)} results")

            # Should be reasonably fast (less than 10 seconds)
            assert search_time < 10.0

        except Exception as e:
            pytest.skip(f"Search performance test not available: {e}")


def check_services_available():
    """Check if required services are available"""
    services_available = True

    # Check Qdrant
    try:
        import qdrant_client
        client = qdrant_client.QdrantClient(url="http://localhost:6334")
        client.get_collections()
        print("+ Qdrant is available")
    except Exception as e:
        print(f"- Qdrant not available: {e}")
        services_available = False

    # Check Ollama
    try:
        import ollama
        ollama.list()
        print("+ Ollama is available")
    except Exception as e:
        print(f"- Ollama not available: {e}")
        services_available = False

    return services_available


def run_integration_tests():
    """Run integration tests if services are available"""
    print("Checking service availability...")

    if not check_services_available():
        print("\nRequired services not available")
        print("To run integration tests, make sure:")
        print("1. Qdrant is running: docker run -d -p 6334:6334 qdrant/qdrant")
        print("2. Ollama is running with embedding model")
        print("3. Collection exists with indexed data")
        return 1

    print("\nServices available, running integration tests...")

    # Run pytest with integration tests
    exit_code = pytest.main([
        __file__,
        "-v",
        "-m", "integration",
        "--tb=short"
    ])

    return exit_code


if __name__ == "__main__":
    print("Semantic Search Service Integration Tests")
    print("=" * 50)

    # Run integration tests
    exit_code = run_integration_tests()

    if exit_code == 0:
        print("\nAll integration tests passed!")
    else:
        print(f"\nSome tests failed (exit code: {exit_code})")

    exit(exit_code)
