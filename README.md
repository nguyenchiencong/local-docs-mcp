# Local Docs MCP - Semantic Search System

A modular semantic search system with MCP (Model Context Protocol) integration for indexing and searching local documentation.

## Quick Start

### Installation

1. **Clone and setup the project:**
```bash
git clone git@github.com:nguyenchiencong/local-docs-mcp.git
cd local-docs-mcp
```

2. **Start required services:**
```bash
# Start Qdrant
docker run -d -p 6334:6334 -p 6333:6333 qdrant/qdrant

# Make sure Ollama is running with the embedding model
ollama pull hf.co/Qwen/Qwen3-Embedding-0.6B-GGUF:F16

# Setup postgres for cocoindex
docker compose -f <(curl -L https://raw.githubusercontent.com/cocoindex-io/cocoindex/refs/heads/main/dev/postgres.yaml) up -d
```

3. **Configure environment:**
```bash
cp config/default.env.example .env
# Edit .env with your specific configuration
```

4. **Index your documents:**
```bash
uv run python -m src.indexing.main_flow
```

5. **Start the MCP server:**
```bash
uv run python -m src.mcp.server
```

## Configuration

### MCP Client Setup

Add this to your MCP client configuration (e.g., Claude Code):

```json
{
  "mcpServers": {
    "semantic-search": {
      "command": "uv",
      "args": ["run", "python", "-m", "/path/to/src.mcp.server"]
    }
  }
}
```

## MCP Tools

The MCP server exposes the following semantic search tools to AI assistants:

| Tool | Purpose | Parameters | Example Prompt |
|------|---------|------------|----------------|
| `semantic_search` | Perform semantic search on indexed documents. Finds content based on meaning and context rather than exact keywords. | `query` (required string), `limit` (optional number, default: 10), `min_similarity_score` (optional number, default: 0.0) | "Find information about error handling patterns in the codebase" |
| `hybrid_search` | Combine semantic search with keyword matching. Useful when exact terminology matters alongside conceptual meaning. | `query` (required string), `semantic_weight` (optional number, default: 0.7), `limit` (optional number, default: 10), `min_similarity_score` (optional number, default: 0.0) | "Search for 'async await' patterns and asynchronous programming concepts" |
| `document_retrieval` | Retrieve complete document by ID. Use this when you need the full context of a specific document found in search results. | `document_id` (required string) | "Get the full document for ID 'doc_12345'" |
| `search_with_metadata_filter` | Search with metadata constraints. Use this to narrow down search results by specific document properties. | `query` (required string), `metadata_filter` (optional object), `limit` (optional number, default: 10), `min_similarity_score` (optional number, default: 0.0) | "Search for API documentation in files with filename containing 'api'" |
| `get_collection_info` | Get information about the indexed document collection, including statistics and status. | _none_ | "Show me collection statistics and indexing status" |

## Development

### Running Tests

```bash
uv run pytest tests/
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Related Projects

- [CocoIndex](https://cocoindex.io/) - Document indexing and processing
- [Qdrant](https://qdrant.tech/) - Vector database for similarity search
- [Ollama](https://ollama.ai/) - Local AI model serving
- [Model Context Protocol](https://modelcontextprotocol.io/) - Standard for AI tool integration
