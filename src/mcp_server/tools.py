"""
MCP tool definitions for semantic search operations.

This module defines all the tools that the MCP server exposes to clients,
including semantic search, hybrid search, document retrieval, and collection management.
"""

import json
import logging
from typing import List, Dict, Any

# Import from the external MCP package (now no naming conflict)
import mcp.types as mcp_types
from mcp.types import TextContent, CallToolResult

# Use Tool from the external mcp package
Tool = mcp_types.Tool

# Handle imports for both package and test contexts
try:
    # Try relative imports first (normal package usage)
    from ..search.service import SemanticSearchService
    from ..search.models import SearchResult, SearchConfig
except ImportError:
    # Fallback to absolute imports (for testing/dynamic loading)
    from search.service import SemanticSearchService
    from search.models import SearchResult, SearchConfig

logger = logging.getLogger(__name__)


def serialize_search_result(result: SearchResult) -> Dict[str, Any]:
    """Convert SearchResult to dictionary for JSON serialization"""
    return {
        "id": result.id,
        "filename": result.filename,
        "text": result.text,
        "score": result.score,
        "location": result.location,
        "token_count": result.token_count,
        "start_index": result.start_index,
        "end_index": result.end_index
    }


def get_available_tools() -> List[Tool]:
    """List available semantic search tools"""
    return [
        Tool(
            name="semantic_search",
            description="Perform semantic search on indexed documents. Finds content based on meaning and context rather than exact keywords.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query - use natural language to describe what you're looking for"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results to return (default: 10)",
                        "default": 10,
                        "minimum": 1,
                        "maximum": 50
                    },
                    "min_similarity_score": {
                        "type": "number",
                        "description": "Minimum similarity score threshold (0.0-1.0, default: 0.0)",
                        "default": 0.0,
                        "minimum": 0.0,
                        "maximum": 1.0
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="hybrid_search",
            description="Combine semantic search with keyword matching. Useful when exact terminology matters alongside conceptual meaning.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query - can include specific terms and conceptual descriptions"
                    },
                    "semantic_weight": {
                        "type": "number",
                        "description": "Weight for semantic search vs keyword matching (0.0-1.0, where 1.0 is pure semantic, default: 0.7)",
                        "default": 0.7,
                        "minimum": 0.0,
                        "maximum": 1.0
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results to return (default: 10)",
                        "default": 10,
                        "minimum": 1,
                        "maximum": 50
                    },
                    "min_similarity_score": {
                        "type": "number",
                        "description": "Minimum similarity score threshold (0.0-1.0, default: 0.0)",
                        "default": 0.0,
                        "minimum": 0.0,
                        "maximum": 1.0
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="document_retrieval",
            description="Retrieve complete document by ID. Use this when you need the full context of a specific document found in search results.",
            inputSchema={
                "type": "object",
                "properties": {
                    "document_id": {
                        "type": "string",
                        "description": "Unique identifier of the document to retrieve"
                    }
                },
                "required": ["document_id"]
            }
        ),
        Tool(
            name="search_with_metadata_filter",
            description="Search with metadata constraints. Use this to narrow down search results by specific document properties.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query"
                    },
                    "metadata_filter": {
                        "type": "object",
                        "description": "Metadata filters to apply (e.g., {'filename': 'tutorial.md', 'document_type': 'tutorial'})",
                        "properties": {
                            "filename": {"type": "string"},
                            "document_type": {"type": "string"},
                            "category": {"type": "string"},
                            "author": {"type": "string"},
                            "version": {"type": "string"},
                            "language": {"type": "string"}
                        },
                        "additionalProperties": True
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results to return (default: 10)",
                        "default": 10,
                        "minimum": 1,
                        "maximum": 50
                    },
                    "min_similarity_score": {
                        "type": "number",
                        "description": "Minimum similarity score threshold (0.0-1.0, default: 0.0)",
                        "default": 0.0,
                        "minimum": 0.0,
                        "maximum": 1.0
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="get_collection_info",
            description="Get information about the indexed document collection, including statistics and status.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        )
    ]


def handle_tool_call(search_service: SemanticSearchService, name: str, arguments: Dict[str, Any]) -> CallToolResult:
    """Handle tool calls for semantic search operations"""

    try:
        if name == "semantic_search":
            query = arguments.get("query")
            limit = arguments.get("limit", 10)
            min_similarity_score = arguments.get("min_similarity_score", 0.0)

            if not query:
                return CallToolResult(
                    content=[TextContent(type="text", text="Error: 'query' parameter is required")],
                    isError=True
                )

            results = search_service.semantic_search(
                query=query,
                limit=limit,
                min_similarity_score=min_similarity_score
            )

            serialized_results = [serialize_search_result(r) for r in results]

            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=json.dumps({
                            "query": query,
                            "results": serialized_results,
                            "total_results": len(serialized_results),
                            "search_type": "semantic"
                        }, indent=2)
                    )
                ]
            )

        elif name == "hybrid_search":
            query = arguments.get("query")
            semantic_weight = arguments.get("semantic_weight", 0.7)
            limit = arguments.get("limit", 10)
            min_similarity_score = arguments.get("min_similarity_score", 0.0)

            if not query:
                return CallToolResult(
                    content=[TextContent(type="text", text="Error: 'query' parameter is required")],
                    isError=True
                )

            results = search_service.hybrid_search(
                query=query,
                semantic_weight=semantic_weight,
                limit=limit,
                min_similarity_score=min_similarity_score
            )

            serialized_results = [serialize_search_result(r) for r in results]

            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=json.dumps({
                            "query": query,
                            "results": serialized_results,
                            "total_results": len(serialized_results),
                            "search_type": "hybrid",
                            "semantic_weight": semantic_weight
                        }, indent=2)
                    )
                ]
            )

        elif name == "document_retrieval":
            document_id = arguments.get("document_id")

            if not document_id:
                return CallToolResult(
                    content=[TextContent(type="text", text="Error: 'document_id' parameter is required")],
                    isError=True
                )

            document = search_service.document_retrieval(document_id)

            if document is None:
                return CallToolResult(
                    content=[TextContent(type="text", text=f"Document with ID '{document_id}' not found")],
                    isError=True
                )

            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=json.dumps(document, indent=2)
                    )
                ]
            )

        elif name == "search_with_metadata_filter":
            query = arguments.get("query")
            metadata_filter = arguments.get("metadata_filter", {})
            limit = arguments.get("limit", 10)
            min_similarity_score = arguments.get("min_similarity_score", 0.0)

            if not query:
                return CallToolResult(
                    content=[TextContent(type="text", text="Error: 'query' parameter is required")],
                    isError=True
                )

            results = search_service.search_with_metadata_filter(
                query=query,
                metadata_filter=metadata_filter,
                limit=limit,
                min_similarity_score=min_similarity_score
            )

            serialized_results = [serialize_search_result(r) for r in results]

            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=json.dumps({
                            "query": query,
                            "metadata_filter": metadata_filter,
                            "results": serialized_results,
                            "total_results": len(serialized_results),
                            "search_type": "filtered"
                        }, indent=2)
                    )
                ]
            )

        elif name == "get_collection_info":
            info = search_service.get_collection_info()

            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=json.dumps(info, indent=2)
                    )
                ]
            )

        else:
            return CallToolResult(
                content=[TextContent(type="text", text=f"Unknown tool: {name}")],
                isError=True
            )

    except Exception as e:
        logger.error(f"Error in tool {name}: {str(e)}")
        return CallToolResult(
            content=[TextContent(type="text", text=f"Error: {str(e)}")],
            isError=True
        )