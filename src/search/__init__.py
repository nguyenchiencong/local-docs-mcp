"""
Search module for semantic search operations.

This module provides search capabilities including:
- Semantic search using vector similarity
- Hybrid search combining semantic and keyword matching
- Document retrieval by ID
- Metadata-filtered search
"""

from .service import SemanticSearchService
from .models import SearchResult, SearchConfig

__all__ = ["SemanticSearchService", "SearchResult", "SearchConfig"]