"""Command-line interface for local-docs-mcp.

Supports:
- `local-docs-mcp` or `local-docs-mcp server` to start the MCP server.
- `local-docs-mcp <tool> ...` to run a single MCP tool once and exit.
"""

import argparse
import asyncio
import json
import sys
from typing import Any, Dict, List, Optional

from .bootstrap import build_search_service
from .mcp_server import server as mcp_server
from .mcp_server.tools import serialize_search_result
from .search.service import SemanticSearchService

AVAILABLE_TOOLS = {
    "semantic_search": "Perform semantic search",
    "hybrid_search": "Combine semantic and keyword search",
    "document_retrieval": "Retrieve a document by ID",
    "search_with_metadata_filter": "Search with metadata constraints",
    "get_collection_info": "Show collection statistics",
}


def _truncate_text(text: str, max_length: int = 180) -> str:
    """Trim long text for console display."""
    normalized = " ".join(text.split())
    if len(normalized) <= max_length:
        return normalized
    return normalized[: max_length - 3] + "..."


def parse_metadata_filter(raw_filter: Optional[str]) -> Dict[str, Any]:
    """Parse metadata filter JSON from CLI input."""
    if not raw_filter:
        return {}
    try:
        parsed = json.loads(raw_filter)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid metadata filter JSON: {exc}") from exc
    if not isinstance(parsed, dict):
        raise ValueError("Metadata filter must be a JSON object.")
    return parsed


def format_search_results(payload: Dict[str, Any]) -> str:
    """Pretty-print search results for the console."""
    query = payload.get("query", "")
    search_type = payload.get("search_type", "search")
    results: List[Dict[str, Any]] = payload.get("results", [])
    header = f"{search_type} results for query: {query} (showing {len(results)})"
    lines = [header]

    for idx, item in enumerate(results, start=1):
        score = item.get("score", 0.0)
        filename = item.get("filename", "") or ""
        doc_id = item.get("id", "")
        location = item.get("location")
        location_suffix = f" @ {location}" if location is not None else ""
        snippet = _truncate_text(item.get("text", ""))
        lines.append(f"{idx}. [{score:.3f}] {filename}{location_suffix} (id={doc_id})")
        if snippet:
            lines.append(f"    {snippet}")

    return "\n".join(lines)


def format_document_output(document: Dict[str, Any]) -> str:
    """Pretty-print a single document retrieval result."""
    lines = [
        f"Document ID: {document.get('id', '')}",
        f"Filename: {document.get('filename', '')}",
    ]
    location = document.get("location")
    if location is not None:
        lines.append(f"Location: {location}")
    token_count = document.get("token_count")
    if token_count is not None:
        lines.append(f"Tokens: {token_count}")
    snippet = _truncate_text(document.get("text", ""), 240)
    if snippet:
        lines.append(f"Content: {snippet}")
    return "\n".join(lines)


def format_collection_output(info: Dict[str, Any]) -> str:
    """Pretty-print collection info."""
    lines = ["Collection info:"]
    for key in sorted(info.keys()):
        lines.append(f"- {key}: {info[key]}")
    return "\n".join(lines)


def run_server() -> int:
    """Start the MCP server (stdio)."""
    asyncio.run(mcp_server.main())
    return 0


def run_mcp_command(
    args: argparse.Namespace,
    search_service: Optional[SemanticSearchService] = None,
) -> int:
    """Execute a single MCP tool from the CLI."""
    service = search_service or build_search_service()
    tool = args.command

    try:
        if tool == "semantic_search":
            if not args.query:
                print("Error: --query is required for semantic_search", file=sys.stderr)
                return 1
            results = service.semantic_search(
                query=args.query,
                limit=args.limit,
                min_similarity_score=args.min_similarity_score,
            )
            payload: Dict[str, Any] = {
                "query": args.query,
                "results": [serialize_search_result(r) for r in results],
                "total_results": len(results),
                "search_type": "semantic_search",
            }

        elif tool == "hybrid_search":
            if not args.query:
                print("Error: --query is required for hybrid_search", file=sys.stderr)
                return 1
            results = service.hybrid_search(
                query=args.query,
                semantic_weight=args.semantic_weight,
                limit=args.limit,
                min_similarity_score=args.min_similarity_score,
            )
            payload = {
                "query": args.query,
                "results": [serialize_search_result(r) for r in results],
                "total_results": len(results),
                "search_type": "hybrid_search",
                "semantic_weight": args.semantic_weight,
            }

        elif tool == "document_retrieval":
            if not args.document_id:
                print("Error: --document-id is required for document_retrieval", file=sys.stderr)
                return 1
            document = service.document_retrieval(args.document_id)
            if document is None:
                print(f"Document with ID '{args.document_id}' not found.", file=sys.stderr)
                return 1
            payload = document

        elif tool == "search_with_metadata_filter":
            if not args.query:
                print("Error: --query is required for search_with_metadata_filter", file=sys.stderr)
                return 1
            try:
                metadata_filter = parse_metadata_filter(args.metadata_filter)
            except ValueError as exc:
                print(f"Error: {exc}", file=sys.stderr)
                return 1

            results = service.search_with_metadata_filter(
                query=args.query,
                metadata_filter=metadata_filter,
                limit=args.limit,
                min_similarity_score=args.min_similarity_score,
            )
            payload = {
                "query": args.query,
                "metadata_filter": metadata_filter,
                "results": [serialize_search_result(r) for r in results],
                "total_results": len(results),
                "search_type": "search_with_metadata_filter",
            }

        elif tool == "get_collection_info":
            payload = service.get_collection_info()

        else:
            print(f"Unknown tool: {tool}", file=sys.stderr)
            return 1

    except Exception as exc:  # pragma: no cover - defensive path
        print(f"Error running tool {tool}: {exc}", file=sys.stderr)
        return 1

    if getattr(args, "json_output", False):
        print(json.dumps(payload, indent=2))
        return 0

    if tool in {"semantic_search", "hybrid_search", "search_with_metadata_filter"}:
        print(format_search_results(payload))
    elif tool == "document_retrieval":
        print(format_document_output(payload))
    elif tool == "get_collection_info":
        print(format_collection_output(payload))
    else:
        # Should be unreachable because of the earlier check.
        print(payload)

    return 0


def build_parser() -> argparse.ArgumentParser:
    """Create the top-level CLI parser."""
    parser = argparse.ArgumentParser(
        prog="local-docs-mcp",
        description="CLI for local-docs-mcp: run MCP tools or start the MCP server.",
    )

    subparsers = parser.add_subparsers(dest="command")

    server_parser = subparsers.add_parser(
        "server",
        help="Start the MCP server (default when no subcommand is provided).",
    )
    server_parser.set_defaults(command="server")

    # Add subparsers for each tool so the tool name can be used directly
    for tool_name, tool_help in AVAILABLE_TOOLS.items():
        tool_parser = subparsers.add_parser(
            tool_name,
            help=f"{tool_help} ({tool_name})",
        )
        tool_parser.set_defaults(command=tool_name)
        tool_parser.add_argument(
            "--json",
            dest="json_output",
            action="store_true",
            help="Output raw JSON.",
        )

        if tool_name in {"semantic_search", "hybrid_search", "search_with_metadata_filter"}:
            tool_parser.add_argument(
                "--query",
                type=str,
                help="Query text for search tools.",
            )
            tool_parser.add_argument(
                "--limit",
                dest="limit",
                type=int,
                help="Maximum number of results to return.",
            )
            tool_parser.add_argument(
                "--min-similarity-score",
                dest="min_similarity_score",
                type=float,
                help="Minimum similarity score threshold.",
            )

        if tool_name == "hybrid_search":
            tool_parser.add_argument(
                "--semantic-weight",
                dest="semantic_weight",
                type=float,
                help="Semantic weight for hybrid search (0.0-1.0).",
            )

        if tool_name == "search_with_metadata_filter":
            tool_parser.add_argument(
                "--metadata-filter",
                dest="metadata_filter",
                type=str,
                help="JSON object to filter search results.",
            )

        if tool_name == "document_retrieval":
            tool_parser.add_argument(
                "--document-id",
                dest="document_id",
                type=str,
                help="Document ID to retrieve.",
            )

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    """CLI entry point."""
    parser = build_parser()
    args = parser.parse_args(argv)

    # Default behavior: start server when no subcommand is provided
    if not getattr(args, "command", None):
        args.command = "server"

    if args.command == "server":
        return run_server()
    if args.command in AVAILABLE_TOOLS:
        return run_mcp_command(args)

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
