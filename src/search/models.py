"""
Data models for the semantic search system.

This module defines the core data structures used throughout the search system
including search results, configuration, and related data classes.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class SearchResult:
    """Represents a single search result"""
    id: str
    filename: str
    text: str
    score: float
    embedding: List[float]
    location: int
    token_count: Optional[int] = None
    start_index: Optional[int] = None
    end_index: Optional[int] = None


@dataclass
class SearchConfig:
    """Configuration for semantic search service"""
    qdrant_url: str = "http://localhost:6334"
    qdrant_collection: str = "local-docs-collection"
    embedding_model: str = "hf.co/Qwen/Qwen3-Embedding-0.6B-GGUF:F16"
    embedding_url: str = "http://localhost:11434"
    default_limit: int = 10
    default_similarity_threshold: float = 0.0