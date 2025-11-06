"""
Semantic Search MCP Server

This MCP server provides semantic search tools using the decoupled semantic search service.
It exposes various search capabilities through the Model Context Protocol.
"""

import asyncio
import json
import logging
from typing import List, Dict, Any
from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp import Resource
from mcp.types import (
    TextContent, ReadResourceRequest, ReadResourceResult,
    ListResourcesRequest, ListResourcesResult, ListToolsRequest, ListToolsResult,
    CallToolResult
)

from ..search.service import SemanticSearchService
from ..search.models import SearchConfig
from ..config import config
from .tools import get_available_tools, handle_tool_call

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize MCP server
server = Server("local-docs-mcp")

# Initialize semantic search service with centralized config
search_config = SearchConfig(config)
search_service = SemanticSearchService(search_config)


@server.list_tools()
async def handle_list_tools() -> ListToolsResult:
    """List available semantic search tools"""
    tools = get_available_tools()
    return ListToolsResult(tools=tools)


@server.call_tool()
async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> CallToolResult:
    """Handle tool calls for semantic search operations"""
    return handle_tool_call(search_service, name, arguments)


@server.list_resources()
async def handle_list_resources() -> ListResourcesResult:
    """List available resources"""
    resources = [
        Resource(
            uri="local-docs-mcp://collection-info",
            name="Collection Information",
            description="Information about the indexed document collection",
            mimeType="application/json"
        )
    ]
    return ListResourcesResult(resources=resources)


@server.read_resource()
async def handle_read_resource(uri: str) -> ReadResourceResult:
    """Handle resource requests"""
    if uri == "local-docs-mcp://collection-info":
        info = search_service.get_collection_info()
        return ReadResourceResult(
            contents=[
                TextContent(
                    type="text",
                    text=json.dumps(info, indent=2)
                )
            ]
        )
    else:
        raise ValueError(f"Unknown resource: {uri}")


async def main():
    """Main entry point for the MCP server"""
    # Use stdio server for MCP communication
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="local-docs-mcp",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={}
                ),
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())