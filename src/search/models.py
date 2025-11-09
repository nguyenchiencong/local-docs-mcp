"""
Data models for the semantic search system.

This module defines the core data structures used throughout the search system
including search results, configuration, and related data classes.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass

try:
    from ..config import config as global_config
except ImportError:
    from config import config as global_config


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

    def __init__(self, config_dict: Optional[Dict[str, Any]] = None, **overrides: Any):
        """Initialize from centralized configuration dictionary with optional overrides"""
        merged_config: Dict[str, Any] = dict(global_config)

        if config_dict:
            merged_config.update(config_dict)

        if overrides:
            merged_config.update(overrides)

        # Support legacy parameter names used in tests (embedding_url)
        if "embedding_url" in merged_config:
            merged_config["ollama_url"] = merged_config["embedding_url"]

        # Backwards compatibility for older parameter names
        if "embedding_model" in merged_config:
            merged_config["ollama_model"] = merged_config["embedding_model"]

        if "default_limit" in merged_config:
            merged_config["search_limit"] = merged_config["default_limit"]

        if "default_similarity_threshold" in merged_config:
            merged_config["similarity_threshold"] = merged_config["default_similarity_threshold"]

        self.qdrant_url = merged_config.get("qdrant_url", "http://localhost:6334")
        self.qdrant_collection = merged_config.get("qdrant_collection", "local-docs-collection")
        self.embedding_model = merged_config.get("ollama_model", "hf.co/Qwen/Qwen3-Embedding-0.6B-GGUF:F16")
        self.embedding_url = merged_config.get("ollama_url", "http://localhost:11434")
        self.default_limit = merged_config.get("search_limit", 10)
        self.default_similarity_threshold = merged_config.get("similarity_threshold", 0.15)
        self.search_hnsw_ef = merged_config.get("search_hnsw_ef", 256)
        self.hybrid_semantic_weight = merged_config.get("hybrid_semantic_weight", 0.85)
        self.mmr_lambda = merged_config.get("mmr_lambda", 0.75)
        self.embedding_dimension = merged_config.get("embedding_dimension", 1024)
