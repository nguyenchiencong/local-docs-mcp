## Project Overview

This is a modular semantic search system with MCP (Model Context Protocol) integration for indexing and searching local documentation using Qdrant vector database and Ollama embeddings. The system provides AI assistants with semantic search capabilities through the Model Context Protocol.

## Key Commands

### Development Setup
```bash
# Install dependencies and set up the project
uv run python scripts/setup.py

# Copy environment configuration and customize
copy config/default.env.example .env
```

### Indexing Documents
```bash
# Index documents from the docs/ directory
uv run python -m src.indexing.main_flow

# Alternative using the project script
local-docs-index
```

### Running the MCP Server
```bash
# Start the MCP server for AI assistant integration
uv run python -m src.mcp_server.server

# Alternative using the project script
local-docs-mcp
```

### Testing
```bash
# Run the test suite
uv run python scripts/run_tests.py

# Run tests with pytest directly (if available)
pytest tests/
```

### External Services (Required Dependencies)
```bash
# Start Qdrant vector database
docker run -d -p 6334:6334 -p 6333:6333 qdrant/qdrant

# Pull Ollama embedding model
ollama pull hf.co/Qwen/Qwen3-Embedding-0.6B-GGUF:F16
```

## Architecture Overview

### Core Components

1. **Indexing Module** (`src/indexing/`)
   - `main_flow.py`: Main CocoIndex flow for document processing and embedding generation
   - `chunking.py`: Text chunking utilities using Chonkie library

2. **Search Service** (`src/search/`)
   - `service.py`: Decoupled semantic search service with various search strategies
   - `models.py`: Data models for search results and configuration

3. **MCP Server** (`src/mcp/`)
   - `server.py`: MCP server implementation exposing search tools
   - `tools.py`: MCP tool definitions and handlers

### Data Flow

```
Documents → CocoIndex → Text Chunking → Ollama Embeddings → Qdrant Storage
                                                            ↓
AI Assistant ← MCP Server ← Semantic Search Service ← Qdrant Query
```

### Configuration

- **Environment Variables**: Set in `.env` file (copy from `config/default.env.example`)
- **MCP Configuration**: `config/mcp_config.json` contains server configuration
- **Project Settings**: `pyproject.toml` contains dependencies and build configuration

### Key Dependencies

- **cocoindex**: Document processing and indexing framework
- **qdrant-client**: Vector database client
- **ollama**: Local AI model serving
- **mcp**: Model Context Protocol library
- **chonkie**: Text chunking library

## Development Notes

### Document Indexing

- Documents are sourced from the `docs/` directory by default
- Text is chunked using Chonkie library before embedding
- Embeddings are generated using Ollama with the specified model
- Results are stored in Qdrant collection named "local-docs-collection"

### Search Capabilities

The system provides multiple search strategies:
- **semantic_search**: Pure semantic similarity search
- **hybrid_search**: Combines semantic with keyword matching
- **document_retrieval**: Retrieve documents by ID
- **search_with_metadata_filter**: Search with metadata constraints

### MCP Integration

The MCP server exposes semantic search tools to AI assistants through:
- Tool definitions in `src/mcp/tools.py`
- Server implementation in `src/mcp/server.py`
- Resource endpoints for collection information

### File Structure Conventions

- Source code follows Python module structure with `__init__.py` files
- Configuration files are in `config/` directory
- Documentation to be indexed goes in `docs/` directory
- Tests are organized in `tests/` directory

### Environment Setup

The project requires these services to be running:
1. Qdrant vector database (default: http://localhost:6334)
2. Ollama with embedding model loaded
3. Environment variables configured in `.env` file

## Common Development Tasks

### Adding New Search Strategies
Add methods to `src/search/service.py` in the `SemanticSearchService` class.

### Adding New MCP Tools
Define tools in `src/mcp/tools.py` and implement handlers in the `handle_tool_call` function.

### Modifying Document Processing
Update the `text_embedding_flow` function in `src/indexing/main_flow.py`.

### Testing Search Functionality
Use the interactive mode in `src/indexing/main_flow.py` or test through the MCP server.

## Rules
- ALWAYS use uv for all python commands
- NEVER run linux bash commands, you must ALWAYS use powershell for commands on windows
- NEVER use emoji