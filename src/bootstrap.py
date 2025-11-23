"""Shared initialization helpers for CLI and MCP server."""

from typing import Any, Dict, Optional

from .config import config as base_config
from .search.models import SearchConfig
from .search.service import SemanticSearchService


def build_search_config(overrides: Optional[Dict[str, Any]] = None) -> SearchConfig:
    """Create a SearchConfig using the global config plus optional overrides."""
    merged: Dict[str, Any] = dict(base_config)
    if overrides:
        merged.update(overrides)
    return SearchConfig(merged)


def build_search_service(
    overrides: Optional[Dict[str, Any]] = None,
) -> SemanticSearchService:
    """Create a SemanticSearchService using shared configuration."""
    search_config = build_search_config(overrides)
    return SemanticSearchService(search_config)

