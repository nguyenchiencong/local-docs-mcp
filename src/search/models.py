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


class SearchConfig:
    """Configuration for semantic search service using centralized config"""

    def __init__(self, config_dict: Dict[str, Any]):
        """Initialize from centralized configuration dictionary"""
        self.qdrant_url = config_dict["qdrant_url"]
        self.qdrant_collection = config_dict["qdrant_collection"]
        self.embedding_model = config_dict["ollama_model"]
        self.embedding_url = config_dict["ollama_url"]
        self.default_limit = config_dict["search_limit"]
        self.default_similarity_threshold = 0.0