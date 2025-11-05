# MCP Usage Guide

This guide explains how to use the Local Docs MCP server with various AI assistants and tools.

## Supported MCP Clients

### Claude Desktop

1. **Install Claude Desktop** from [Anthropic](https://claude.ai/download)

2. **Configure MCP Server** by adding to your Claude Desktop config:

   **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
   **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

   ```json
   {
     "mcpServers": {
       "semantic-search": {
         "command": "python",
         "args": ["-m", "src.mcp_server.server"],
         "env": {
           "QDRANT_URL": "http://localhost:6334",
           "QDRANT_COLLECTION": "local-docs-collection",
           "OLLAMA_MODEL": "hf.co/Qwen/Qwen3-Embedding-0.6B-GGUF:F16"
         }
       }
     }
   }
   ```

3. **Restart Claude Desktop** to load the MCP server

### Continue.dev

Add to your `config.json`:

```json
{
  "mcpServers": {
    "semantic-search": {
      "command": "python",
      "args": ["-m", "src.mcp_server.server"],
      "env": {
        "QDRANT_URL": "http://localhost:6334",
        "QDRANT_COLLECTION": "local-docs-collection",
        "OLLAMA_MODEL": "hf.co/Qwen/Qwen3-Embedding-0.6B-GGUF:F16"
      }
    }
  }
}
```

## Available Tools

### 1. semantic_search

Search for documents based on meaning and context rather than exact keywords.

**Parameters:**
- `query` (required): Search query in natural language
- `limit` (optional): Maximum results to return (1-50, default: 10)
- `min_similarity_score` (optional): Minimum similarity threshold (0.0-1.0, default: 0.0)

**Example:**
```
Search for information about user authentication and security best practices
```

### 2. hybrid_search

Combine semantic search with keyword matching for more precise results.

**Parameters:**
- `query` (required): Search query
- `semantic_weight` (optional): Balance between semantic and keyword (0.0-1.0, default: 0.7)
- `limit` (optional): Maximum results to return (1-50, default: 10)
- `min_similarity_score` (optional): Minimum similarity threshold (0.0-1.0, default: 0.0)

**Example:**
```
Find information about Node.get_tree() function and scene hierarchy management
```

### 3. document_retrieval

Retrieve complete document by ID when you need full context.

**Parameters:**
- `document_id` (required): Unique identifier of the document

**Example:**
```
Get the complete document with ID: 12345678-1234-1234-1234-123456789012
```

### 4. search_with_metadata_filter

Search with metadata constraints to narrow down results.

**Parameters:**
- `query` (required): Search query
- `metadata_filter` (optional): Dictionary of metadata filters
- `limit` (optional): Maximum results to return (1-50, default: 10)
- `min_similarity_score` (optional): Minimum similarity threshold (0.0-1.0, default: 0.0)

**Example:**
```
Search for animation tutorials with metadata filter: {"category": "tutorial", "topic": "animation"}
```

### 5. get_collection_info

Get statistics and status information about the indexed document collection.

**Parameters:** None

## Usage Examples

### For Code Documentation

```
I need to understand how to implement a character controller in Godot. Can you search for relevant documentation?
```

### For Learning and Tutorials

```
Find tutorials about 2D sprite animation and movement mechanics
```

### For Troubleshooting

```
Search for information about common physics engine issues and their solutions
```

### For API Reference

```
Look up the Node class methods and properties, specifically focusing on tree traversal
```

## Best Practices

1. **Use Natural Language**: Describe what you're looking for in natural terms rather than exact keywords
2. **Be Specific**: Include relevant context like specific functions, classes, or concepts
3. **Iterate**: Start with broad searches, then refine with more specific queries
4. **Use Metadata Filters**: When you know the document type or category, use filters to narrow results
5. **Check Similarity Scores**: Higher scores indicate more relevant results

## Troubleshooting

### Common Issues

1. **No Results Found**
   - Check if your documents are indexed: `python -m src.indexing.main_flow`
   - Verify Qdrant is running: `docker ps | grep qdrant`
   - Check collection exists: Use `get_collection_info` tool

2. **Low Quality Results**
   - Try rephrasing your query with different terms
   - Adjust similarity threshold
   - Use hybrid search for better keyword matching

3. **Connection Errors**
   - Ensure Qdrant is accessible at `http://localhost:6334`
   - Verify Ollama is running with the correct model
   - Check environment variables in `.env`

### Debug Mode

Enable debug logging by setting:
```bash
LOG_LEVEL=DEBUG
```

## Performance Tips

1. **Batch Queries**: When searching for multiple related topics, consider using broader queries
2. **Appropriate Limits**: Use reasonable limits (5-15) for better performance
3. **Metadata Filtering**: Use filters to reduce search space when possible
4. **Caching**: The MCP server caches Qdrant clients for optimal performance