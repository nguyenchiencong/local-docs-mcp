# Local Docs MCP

A modular semantic search system with MCP (Model Context Protocol) integration for searching local documentation. The Retrieval-Augmented Generation (RAG) system not only lets you manage document chunks for knowledge retrieval but also gives AI assistants semantic search capabilities through the MCP.

## Key Features

| **Core Capability**     | **Technical Implementation**                                                                                                                                                                                                                   |
| :---------------------- | :--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Document Indexing**   | A full indexing pipeline that processes documents from the `docs/` directory, chunks them, and creates embeddings using **Ollama**. With **Cocoindex**, it updates only the parts that have changed — when users edit or add new content, the system detects those changes and updates selectively. |
| **Vector Database**     | Uses **Qdrant** to store document embeddings for semantic search.                                                                                                                                                                              |
| **Retrieval**           | The search service provides semantic search capabilities with multiple strategies (**semantic**, **hybrid**, and **filtered**).                                                                                                                |
| **MCP Integration**     | The **MCP server** exposes these retrieval capabilities to AI assistants.                                                                                                                                                                     |

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
cp .env.example .env
# Edit .env with your specific configuration
```

4. **Install dependencies:**
```bash
uv sync
```

### Usage

Before indexing, add your documents to the docs folder.

**To index your documents:**
```bash
uv run python -m src.indexing.main_flow
# To run the force reindex utility
uv run python -m src.indexing.force_reindex
```

**To start the MCP server:**
```bash
uv run python -m src.mcp_server.server
```

## Configuration

### System Settings

All configuration is managed in [`pyproject.toml`](pyproject.toml#L66) under the `[tool.local-docs]` section:

```toml
[tool.local-docs]
# Qdrant configuration
qdrant_url = "http://localhost:6334"
qdrant_collection = "local-docs-collection"

# Ollama configuration
ollama_url = "http://localhost:11434"
ollama_model = "hf.co/Qwen/Qwen3-Embedding-0.6B-GGUF:F16"
embedding_dimension = 1024

# Document configuration
docs_directory = "docs"
supported_extensions = [".md", ".rst", ".txt"]

# Search configuration
search_limit = 10
```

**Environment Variables**: Override any setting with `LOCAL_DOCS_*` environment variables:
```bash
export LOCAL_DOCS_SEARCH_LIMIT=20
export LOCAL_DOCS_OLLAMA_MODEL="different-model"
```

### MCP Client Setup

Add this to your MCP client configuration (e.g., Claude Code):

```json
{
  "mcpServers": {
    "local-docs-mcp": {
      "command": "uv",
      "args": ["run", "--project", "/path/to/local-docs-mcp", "-m", "src.mcp_server.server"]
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

### Use cases

**Documentation Research:**
- "What are signals and how do they work in Godot?"
- "Find tutorials about character controllers"
- "Explain the difference between KinematicBody and RigidBody"

**Problem Solving:**
- "How do I fix 'node not found' errors?"
- "What are the best practices for performance optimization?"
- "Search for debugging techniques in Godot"

**Learning Paths:**
- "I'm a beginner, show me getting started content"
- "What should I learn after basic GDScript?"
- "Find intermediate tutorials about physics"

**Specific Searches:**
- "Show me the top 5 most relevant results about animations"
- "Find only tutorial files about UI design"
- "Look for performance optimization guides"

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
