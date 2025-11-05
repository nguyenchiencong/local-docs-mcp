# Local Docs MCP - Semantic Search System

A modular semantic search system with MCP (Model Context Protocol) integration for indexing and searching local documentation using Qdrant and Ollama embeddings.

## Quick Start

### Prerequisites

- [Python 3.11+](https://www.python.org/downloads/)
- [Qdrant](https://qdrant.tech/) vector database
- [Ollama](https://ollama.ai/) with embedding model

### Installation

1. **Clone and setup the project:**
   ```bash
   git clone <repository-url>
   cd local-docs-mcp
   python scripts/setup.py
   ```

2. **Start required services:**
   ```bash
   # Start Qdrant
   docker run -d -p 6334:6334 -p 6333:6333 qdrant/qdrant
   
   # Make sure Ollama is running with the embedding model
   ollama pull hf.co/Qwen/Qwen3-Embedding-0.6B-GGUF:F16
   ```

3. **Configure environment:**
   ```bash
   cp config/default.env.example .env
   # Edit .env with your specific configuration
   ```

4. **Index your documents:**
   ```bash
   python -m src.indexing.main_flow
   ```

5. **Start the MCP server:**
   ```bash
   python -m src.mcp.server
   ```

## Configuration

### Environment Variables

Key configuration options in `.env`:

```bash
# Qdrant Configuration
QDRANT_URL=http://localhost:6334
QDRANT_COLLECTION=TextEmbedding

# Ollama Configuration
OLLAMA_MODEL=hf.co/Qwen/Qwen3-Embedding-0.6B-GGUF:F16
```

### MCP Client Setup

Add this to your MCP client configuration (e.g., Claude Desktop):

```json
{
  "mcpServers": {
    "semantic-search": {
      "command": "python",
      "args": ["-m", "src.mcp.server"],
      "env": {
        "QDRANT_URL": "http://localhost:6334",
        "QDRANT_COLLECTION": "local-docs-collection",
        "OLLAMA_MODEL": "hf.co/Qwen/Qwen3-Embedding-0.6B-GGUF:F16"
      }
    }
  }
}
```

## Development

### Running Tests

```bash
python scripts/run_tests.py
```

### Project Structure Benefits

- **Modular Design**: Clear separation of concerns between indexing, search, and MCP functionality
- **Scalable Architecture**: Easy to add new search strategies or MCP tools
- **Testable**: Each module can be tested independently
- **Maintainable**: Organized structure makes code easier to understand and modify

### Adding New Features

1. **New Search Strategies**: Add methods to `src/search/service.py`
2. **New MCP Tools**: Define in `src/mcp/tools.py`
3. **New Indexing Features**: Extend `src/indexing/main_flow.py`

## Available Tools

The MCP server provides these tools:

- **`semantic_search`** - Pure semantic search based on meaning and context
- **`hybrid_search`** - Combines semantic search with keyword matching
- **`document_retrieval`** - Retrieve complete documents by ID
- **`search_with_metadata_filter`** - Search with metadata constraints
- **`get_collection_info`** - Get collection statistics and status

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## License

This project is part of the local-docs-mcp system and follows the same license terms.

## Related Projects

- [CocoIndex](https://cocoindex.io/) - Document indexing and processing
- [Qdrant](https://qdrant.tech/) - Vector database for similarity search
- [Ollama](https://ollama.ai/) - Local AI model serving
- [Model Context Protocol](https://modelcontextprotocol.io/) - Standard for AI tool integration
