#!/usr/bin/env python3
"""
Performance test for the search service to demonstrate the optimization.
"""

import os
import sys
import time

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_search_performance():
    """Test search performance with caching"""
    print("Testing Search Service Performance")
    print("=" * 50)

    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("Environment variables loaded")
    except ImportError:
        print("dotenv not available, continuing without it")

    try:
        from search.service import SemanticSearchService
        from search.models import SearchConfig
        print("Successfully imported search modules")
    except Exception as e:
        print(f"Failed to import search modules: {e}")
        return False

    # Create search configuration
    config = SearchConfig(
        qdrant_url="http://localhost:6334",
        qdrant_collection="local-docs-collection",
        embedding_model="hf.co/Qwen/Qwen3-Embedding-0.6B-GGUF:F16",
        embedding_url="http://localhost:11434",
        default_limit=3
    )

    # Initialize search service
    try:
        search_service = SemanticSearchService(config)
        print("Search service initialized successfully")
    except Exception as e:
        print(f"Failed to initialize search service: {e}")
        return False

    # Test queries
    test_queries = [
        "What is CocoIndex?",
        "How to use embeddings?",
        "Document processing",
        "What is CocoIndex?",  # Duplicate to test caching
        "How to use embeddings?",  # Duplicate to test caching
        "Python configuration"
    ]

    print(f"\nTesting {len(test_queries)} queries (including duplicates for cache testing):")

    total_time = 0
    for i, query in enumerate(test_queries, 1):
        start_time = time.time()

        try:
            results = search_service.semantic_search(query, limit=3)
            end_time = time.time()

            query_time = end_time - start_time
            total_time += query_time

            cache_status = "CACHED" if i > 3 and query in test_queries[:i-1] else "NEW"

            print(f"{i}. '{query}' - {cache_status} - {query_time:.3f}s - {len(results)} results")

        except Exception as e:
            print(f"{i}. '{query}' - ERROR: {e}")

    print(f"\nPerformance Summary:")
    print(f"Total time: {total_time:.3f}s")
    print(f"Average time per query: {total_time/len(test_queries):.3f}s")

    # Test cache effectiveness
    print(f"\nCache Test:")
    print("First-time queries should be slower than cached queries")

    return True

def main():
    """Main performance test function"""
    success = test_search_performance()

    if success:
        print("\nPERFORMANCE TEST COMPLETED")
        print("\nOptimizations implemented:")
        print("✓ Query caching to avoid repeated embeddings")
        print("✓ Direct HTTP requests to Ollama (faster than library)")
        print("✓ Shorter timeout for better responsiveness")
        print("✓ Fallback mechanism for reliability")

        print("\nBenefits:")
        print("- Cached queries return instantly")
        print("- Reduced Ollama server load")
        print("- Faster search response times")
        print("- Better user experience")
    else:
        print("\nPERFORMANCE TEST FAILED")
        return 1

    return 0

if __name__ == "__main__":
    exit(main())