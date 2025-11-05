#!/usr/bin/env python3
"""
Test script for the enhanced hybrid search functionality.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from search.service import SemanticSearchService
from search.models import SearchConfig, SearchResult

def test_term_extraction():
    """Test the _extract_search_terms helper method"""
    print("Testing term extraction...")

    # Create a mock config
    config = SearchConfig(
        qdrant_url="http://localhost:6334",
        qdrant_collection="test-collection",
        embedding_url="http://localhost:11434",
        embedding_model="test-model"
    )

    service = SemanticSearchService(config)

    # Test cases
    test_queries = [
        "how to install python packages",
        "database connection pooling",
        "the quick brown fox jumps over the lazy dog",
        "API authentication with JWT tokens",
        "configuration file setup"
    ]

    for query in test_queries:
        terms = service._extract_search_terms(query)
        print(f"Query: '{query}'")
        print(f"Terms: {terms}")
        print()

def test_keyword_scoring():
    """Test the _calculate_keyword_scores helper method"""
    print("Testing keyword scoring...")

    # Create a mock config
    config = SearchConfig(
        qdrant_url="http://localhost:6334",
        qdrant_collection="test-collection",
        embedding_url="http://localhost:11434",
        embedding_model="test-model"
    )

    service = SemanticSearchService(config)

    # Create mock search results
    mock_results = [
        SearchResult(
            id="doc1",
            filename="setup.md",
            text="This guide explains how to install Python packages using pip. Package installation is essential for Python development.",
            score=0.8,
            embedding=[],
            location=0,
            token_count=20,
            start_index=0,
            end_index=100
        ),
        SearchResult(
            id="doc2",
            filename="database.md",
            text="Database connection pooling improves performance by reusing connections. Most modern databases support connection pooling.",
            score=0.7,
            embedding=[],
            location=0,
            token_count=25,
            start_index=0,
            end_index=120
        ),
        SearchResult(
            id="doc3",
            filename="api.md",
            text="REST API authentication can be implemented using JWT tokens. JWT provides secure token-based authentication.",
            score=0.6,
            embedding=[],
            location=0,
            token_count=22,
            start_index=0,
            end_index=110
        )
    ]

    # Test with different queries
    test_cases = [
        ("python install packages", mock_results),
        ("database connection", mock_results),
        ("API authentication JWT", mock_results),
        ("unrelated terms", mock_results)
    ]

    for query, results in test_cases:
        terms = service._extract_search_terms(query)
        scores = service._calculate_keyword_scores(results, terms)

        print(f"Query: '{query}'")
        print(f"Terms: {terms}")
        print("Keyword scores:")
        for result in results:
            score = scores.get(result.id, 0.0)
            print(f"  {result.id} ({result.filename}): {score:.3f}")
        print()

def main():
    """Run all tests"""
    print("=== Testing Enhanced Hybrid Search Functionality ===\n")

    test_term_extraction()
    print("=" * 50)
    test_keyword_scoring()

    print("Tests completed successfully!")

if __name__ == "__main__":
    main()