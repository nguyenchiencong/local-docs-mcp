# Document Indexing Guide

This guide explains how to index your local documentation using the Local Docs MCP system.

## Overview

The indexing process transforms your local documents into searchable vector embeddings using:

1. **Document Ingestion**: Reads files from your `docs/` directory
2. **Text Chunking**: Splits documents into manageable chunks using Chonkie with TikToken
3. **Embedding Generation**: Creates vector embeddings using Ollama
4. **Vector Storage**: Stores embeddings in Qdrant for fast similarity search

## Prerequisites

Before indexing, ensure:

- [x] Qdrant is running: `docker run -d -p 6334:6334 -p 6333:6333 qdrant/qdrant`
- [x] Ollama is running with embedding model
- [x] Your documents are in the `docs/` directory
- [x] `.cocoignore` is configured (optional)

## Running the Indexing Process

### Method 1: Direct Execution

```bash
python -m src.indexing.main_flow
```

### Method 2: Using CocoIndex CLI

```bash
# Update the index
cocoindex update main

# Preview what will be indexed
cocoindex update main --dry-run
```

### Method 3: Using Setup Script

```bash
python scripts/setup.py
```

## Document Processing

### Supported File Types

The system automatically processes these file types:

- **Markdown** (`.md`, `.markdown`)
- **reStructuredText** (`.rst`)
- **Text** (`.txt`)
- **HTML** (`.html`, `.htm`)

### File Filtering

Use `.cocoignore` to exclude files from indexing:

```
# Exclude binary files
*.png
*.jpg
*.gif
*.pdf

# Exclude directories
.git/
__pycache__/
node_modules/

# Exclude specific files
DRAFT.md
TODO.txt
```

### Chunking Strategy

Documents are chunked using:

- **Tokenizer**: TikToken with `cl100k_base` encoding
- **Chunk Size**: 2000 tokens
- **Overlap**: 500 tokens between chunks
- **Metadata**: Each chunk includes position and token count

## Configuration

### Environment Variables

Key settings in your `.env` file:

```bash
# Qdrant Configuration
QDRANT_URL=http://localhost:6334
QDRANT_COLLECTION=TextEmbedding

# Ollama Configuration
OLLAMA_MODEL=hf.co/Qwen/Qwen3-Embedding-0.6B-GGUF:F16

# Chunking Configuration
CHUNK_SIZE=2000
CHUNK_OVERLAP=500
```

### Customizing Chunking

Modify `src/indexing/chunking.py` for custom chunking:

```python
def chunk_with_chonkie(text: str) -> List[Dict]:
    tokenizer = tiktoken.get_encoding("cl100k_base")
    
    chunker = TokenChunker(
        tokenizer=tokenizer,
        chunk_size=2000,  # Adjust as needed
        chunk_overlap=500  # Adjust as needed
    )
    
    chunks = chunker.chunk(text)
    # ... rest of processing
```

## Monitoring Progress

### During Indexing

The indexing process will show:

```
🔧 Processing documents...
📄 Found 150 documents to process
📊 Chunking documents...
🔢 Generating embeddings...
💾 Storing in Qdrant...
✅ Indexing completed!
```

### Checking Collection Status

Use the MCP tool `get_collection_info` or check Qdrant dashboard at `http://localhost:6333/dashboard`

## Troubleshooting

### Common Issues

1. **No Documents Found**
   ```
   Error: No documents found in docs/ directory
   ```
   **Solution**: Ensure your documents are in the `docs/` directory and not excluded by `.cocoignore`

2. **Embedding Model Not Available**
   ```
   Error: Model not found: hf.co/Qwen/Qwen3-Embedding-0.6B-GGUF:F16
   ```
   **Solution**: Pull the model in Ollama:
   ```bash
   ollama pull hf.co/Qwen/Qwen3-Embedding-0.6B-GGUF:F16
   ```

3. **Qdrant Connection Failed**
   ```
   Error: Connection to Qdrant failed
   ```
   **Solution**: Ensure Qdrant is running and accessible at `http://localhost:6334`

4. **Memory Issues**
   ```
   Error: Out of memory during embedding generation
   ```
   **Solution**: Reduce chunk size or process documents in smaller batches

### Debug Mode

Enable detailed logging:

```bash
LOG_LEVEL=DEBUG python -m src.indexing.main_flow
```

## Performance Optimization

### For Large Document Sets

1. **Batch Processing**: Process documents in smaller groups
2. **Chunk Size**: Optimize chunk size for your content (1000-4000 tokens)
3. **Overlap**: Reduce overlap for faster processing (200-300 tokens)
4. **Hardware**: Ensure sufficient RAM for embedding generation

### For Better Search Quality

1. **Chunk Size**: Larger chunks preserve more context
2. **Overlap**: Higher overlap ensures content continuity
3. **Preprocessing**: Clean and normalize text before indexing
4. **Metadata**: Include relevant metadata in chunks

## Advanced Usage

### Custom Document Sources

Modify `src/indexing/main_flow.py` to use different sources:

```python
# Instead of LocalFile, use other sources
data_scope["documents"] = flow_builder.add_source(
    cocoindex.sources.GitRepository(url="https://github.com/user/repo")
)
```

### Multiple Collections

Index different document types into separate collections:

```python
# In main_flow.py
QDRANT_COLLECTION = "TechnicalDocs"  # or "UserDocs", "API Docs", etc.
```

### Incremental Updates

CocoIndex automatically handles incremental updates:

```bash
# Only processes new or modified files
cocoindex update main
```

## Best Practices

1. **Document Organization**: Structure your docs logically
2. **File Naming**: Use descriptive filenames
3. **Content Quality**: Ensure documents are well-written and structured
4. **Regular Updates**: Reindex when documents change
5. **Monitoring**: Check collection status regularly

## Next Steps

After indexing:

1. **Test Search**: Use the MCP tools to verify search quality
2. **Configure MCP Client**: Set up your AI assistant with the MCP server
3. **Monitor Performance**: Track search quality and system performance
4. **Iterate**: Refine chunking and configuration based on results