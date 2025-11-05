# Configuration Guide

This guide covers all configuration options for the Local Docs MCP system.

## Environment Configuration

### Primary Configuration File

Copy the template and customize:

```bash
cp config/default.env.example .env
```

### Environment Variables

#### Core Settings

```bash
# Qdrant Configuration
QDRANT_URL=http://localhost:6334
QDRANT_COLLECTION=TextEmbedding

# Ollama Configuration
OLLAMA_MODEL=hf.co/Qwen/Qwen3-Embedding-0.6B-GGUF:F16

# Logging Configuration
LOG_LEVEL=INFO

# MCP Server Configuration
MCP_SERVER_NAME=semantic-search
MCP_SERVER_VERSION=1.0.0
```

#### Advanced Settings

```bash
# Chunking Configuration
CHUNK_SIZE=2000
CHUNK_OVERLAP=500
CHUNK_ENCODING=cl100k_base

# Search Configuration
DEFAULT_SEARCH_LIMIT=10
DEFAULT_SIMILARITY_THRESHOLD=0.0
MAX_SEARCH_LIMIT=50

# Performance Configuration
QDRANT_TIMEOUT=30
OLLAMA_TIMEOUT=60
EMBEDDING_BATCH_SIZE=10
```

## MCP Configuration

### Client Configuration

The MCP server configuration is in `config/mcp_config.json`:

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

### Server Configuration

Customize MCP server behavior in `src/mcp/server.py`:

```python
# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize search service with custom config
search_config = SearchConfig(
    qdrant_url=os.getenv("QDRANT_URL", "http://localhost:6334"),
    qdrant_collection=os.getenv("QDRANT_COLLECTION", "local-docs-collection"),
    embedding_model=os.getenv("OLLAMA_MODEL", "hf.co/Qwen/Qwen3-Embedding-0.6B-GGUF:F16"),
    default_limit=int(os.getenv("DEFAULT_SEARCH_LIMIT", "10")),
    default_similarity_threshold=float(os.getenv("DEFAULT_SIMILARITY_THRESHOLD", "0.0"))
)
```

## Qdrant Configuration

### Connection Settings

```python
# In src/search/models.py
@dataclass
class SearchConfig:
    qdrant_url: str = "http://localhost:6334"
    qdrant_collection: str = "local-docs-collection"
    # ... other settings
```

### Collection Configuration

Qdrant collection is automatically created with these settings:

- **Vector Size**: Determined by embedding model (typically 384 or 768)
- **Distance Metric**: Cosine similarity
- **Vector Name**: `text_embedding`

### Advanced Qdrant Settings

For production deployments, consider:

```python
# Custom collection configuration
from qdrant_client.models import VectorParams, Distance

client.create_collection(
    collection_name="local-docs-collection",
    vectors_config=VectorParams(
        size=768,  # Match your embedding model
        distance=Distance.COSINE
    ),
    optimizers_config=OptimizersConfig(
        default_segment_number=2,
        max_segment_size=20000,
        memmap_threshold=50000
    )
)
```

## Ollama Configuration

### Model Selection

Available embedding models:

```bash
# Qwen embeddings (recommended)
ollama pull hf.co/Qwen/Qwen3-Embedding-0.6B-GGUF:F16

# Alternative models
ollama pull nomic-embed-text
ollama pull mxbai-embed-large
```

### Model Configuration

Update model in `.env`:

```bash
# For different models
OLLAMA_MODEL=nomic-embed-text
OLLAMA_MODEL=mxbai-embed-large
```

### Custom Ollama Server

If using a remote Ollama server:

```bash
OLLAMA_BASE_URL=http://your-ollama-server:11434
OLLAMA_MODEL=your-custom-model
```

## Indexing Configuration

### Document Source Configuration

Modify `src/indexing/main_flow.py`:

```python
# Local files
data_scope["documents"] = flow_builder.add_source(
    cocoindex.sources.LocalFile(path="docs")
)

# Git repository
data_scope["documents"] = flow_builder.add_source(
    cocoindex.sources.GitRepository(
        url="https://github.com/user/repo",
        branch="main"
    )
)

# Multiple sources
data_scope["docs"] = flow_builder.add_source(
    cocoindex.sources.LocalFile(path="technical-docs")
)
data_scope["guides"] = flow_builder.add_source(
    cocoindex.sources.LocalFile(path="user-guides")
)
```

### Chunking Configuration

Customize in `src/indexing/chunking.py`:

```python
def chunk_with_chonkie(text: str) -> List[Dict]:
    # Different encoding
    tokenizer = tiktoken.get_encoding("p50k_base")
    
    # Custom chunking parameters
    chunker = TokenChunker(
        tokenizer=tokenizer,
        chunk_size=int(os.getenv("CHUNK_SIZE", "2000")),
        chunk_overlap=int(os.getenv("CHUNK_OVERLAP", "500"))
    )
    
    # Custom processing
    chunks = chunker.chunk(text)
    # ... your custom logic
```

## Search Configuration

### Search Service Configuration

Customize in `src/search/service.py`:

```python
class SemanticSearchService:
    def __init__(self, config: SearchConfig):
        self.config = config
        # Custom initialization
    
    def semantic_search(self, query: str, **kwargs):
        # Custom search logic
        limit = kwargs.get('limit', self.config.default_limit)
        # ... your implementation
```

### Search Parameters

Default search parameters:

```python
# In src/search/models.py
@dataclass
class SearchConfig:
    default_limit: int = 10
    default_similarity_threshold: float = 0.0
    # ... other settings
```

## Logging Configuration

### Basic Logging

```bash
# In .env
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR, CRITICAL
```

### Advanced Logging

Create `config/logging.yaml`:

```yaml
version: 1
disable_existing_loggers: false

formatters:
  standard:
    format: '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
  detailed:
    format: '%(asctime)s [%(levelname)s] %(name)s:%(lineno)d: %(message)s'

handlers:
  console:
    class: logging.StreamHandler
    level: INFO
    formatter: standard
    stream: ext://sys.stdout

  file:
    class: logging.handlers.RotatingFileHandler
    level: DEBUG
    formatter: detailed
    filename: logs/local-docs-mcp.log
    maxBytes: 10485760  # 10MB
    backupCount: 5

loggers:
  src:
    level: DEBUG
    handlers: [console, file]
    propagate: false

root:
  level: INFO
  handlers: [console]
```

Use in your code:

```python
import logging.config
import yaml

with open('config/logging.yaml', 'r') as f:
    config = yaml.safe_load(f)
    logging.config.dictConfig(config)
```

## Performance Configuration

### Caching

Enable Qdrant client caching:

```python
@functools.cache
def get_qdrant_client() -> QdrantClient:
    return QdrantClient(url=self.config.qdrant_url, prefer_grpc=True)
```

### Batch Processing

Configure batch sizes:

```bash
# In .env
EMBEDDING_BATCH_SIZE=10
SEARCH_BATCH_SIZE=5
```

### Connection Pooling

For high-load scenarios:

```python
from qdrant_client import QdrantClient
from qdrant_client.http import models

client = QdrantClient(
    url=qdrant_url,
    prefer_grpc=True,
    timeout=30,
    grpc_options={
        'grpc.keepalive_time_ms': 30000,
        'grpc.keepalive_timeout_ms': 5000,
        'grpc.keepalive_permit_without_calls': True,
        'grpc.http2.max_pings_without_data': 0,
        'grpc.http2.min_time_between_pings_ms': 10000,
        'grpc.http2.min_ping_interval_without_data_ms': 300000
    }
)
```

## Security Configuration

### Environment Security

```bash
# Use environment-specific configs
ENVIRONMENT=development  # development, staging, production

# Production settings
QDRANT_URL=https://your-qdrant-cluster.com
QDRANT_API_KEY=your-api-key
OLLAMA_BASE_URL=https://your-ollama-instance.com
```

### Access Control

For production deployments:

```python
# Add authentication middleware
from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBearer

security = HTTPBearer()

async def verify_token(token: str = Depends(security)):
    # Validate token
    if not validate_token(token.credentials):
        raise HTTPException(status_code=401, detail="Invalid token")
    return token
```

## Development Configuration

### Development Environment

```bash
# .env.development
LOG_LEVEL=DEBUG
QDRANT_URL=http://localhost:6334
OLLAMA_MODEL=hf.co/Qwen/Qwen3-Embedding-0.6B-GGUF:F16
```

### Testing Configuration

```bash
# .env.testing
LOG_LEVEL=DEBUG
QDRANT_URL=http://localhost:6335  # Different port for tests
QDRANT_COLLECTION=TestEmbedding
OLLAMA_MODEL=test-model
```

### Docker Configuration

`docker-compose.yml`:

```yaml
version: '3.8'
services:
  qdrant:
    image: qdrant/qdrant:latest
    ports:
      - "6333:6333"
      - "6334:6334"
    environment:
      - QDRANT__SERVICE__HTTP_PORT=6333
      - QDRANT__SERVICE__GRPC_PORT=6334
    volumes:
      - qdrant_data:/qdrant/storage

  ollama:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama

volumes:
  qdrant_data:
  ollama_data:
```

## Troubleshooting Configuration

### Common Issues

1. **Connection Refused**
   ```bash
   # Check if services are running
   docker ps | grep qdrant
   docker ps | grep ollama
   ```

2. **Model Not Found**
   ```bash
   # List available models
   ollama list
   
   # Pull required model
   ollama pull hf.co/Qwen/Qwen3-Embedding-0.6B-GGUF:F16
   ```

3. **Permission Denied**
   ```bash
   # Check file permissions
   ls -la .env
   chmod 600 .env
   ```

### Debug Configuration

Enable debug mode:

```bash
LOG_LEVEL=DEBUG python -m src.mcp.server
```

Check configuration loading:

```python
import os
from dotenv import load_dotenv

load_dotenv()
print(f"QDRANT_URL: {os.getenv('QDRANT_URL')}")
print(f"OLLAMA_MODEL: {os.getenv('OLLAMA_MODEL')}")