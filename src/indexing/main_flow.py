"""
Main indexing flow for document processing and embedding generation.

This module defines the CocoIndex flow for processing local documents,
chunking them, generating embeddings, and storing them in Qdrant.
"""

import functools
import os
import fnmatch
from pathlib import Path
from typing import List, Union, Optional

import cocoindex
import ollama
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams
from ollama import ResponseError, RequestError

from .chunking import chunk_with_chonkie
from ..config import config


class IndexingError(Exception):
    """Base exception for indexing errors."""
    pass


class OllamaConnectionError(IndexingError):
    """Raised when Ollama connection fails."""
    pass


class QdrantConnectionError(IndexingError):
    """Raised when Qdrant connection fails."""
    pass


# Configuration is now imported from config module

# Configure ollama client
ollama_client = ollama.Client(host=config["ollama_url"])


def load_cocoignore_patterns(file_path: str = config["cocoignore_file"]) -> List[str]:
    """Load patterns from .cocoignore file"""
    patterns = []
    try:
        with open(file_path, 'r') as f:
            for line in f:
                line = line.strip()
                # Skip comments and empty lines
                if line and not line.startswith('#'):
                    patterns.append(line)
        return patterns
    except FileNotFoundError:
        print("Warning: .cocoignore file not found")
        return []


def generate_embedding(text: Union[str, List[str]]) -> Union[List[float], List[List[float]]]:
    """Generate embedding using Ollama model with error handling."""
    try:
        response = ollama_client.embed(
            model=config["ollama_model"],
            input=text
        )
        return response.embeddings if len(response.embeddings) > 1 else response.embeddings[0]
    except ResponseError as e:
        raise OllamaConnectionError(f"Ollama model error: {e.error}")
    except RequestError as e:
        raise OllamaConnectionError(f"Failed to connect to Ollama: {e}. Make sure Ollama is running at: {config['ollama_url']}")


def ensure_qdrant_collection(client: QdrantClient, collection_name: str = config["qdrant_collection"]) -> None:
    """Ensure Qdrant collection exists with correct dimensions."""
    try:
        collection_info = client.get_collection(collection_name)
        if collection_info.config.params.vectors.size != config["embedding_dimension"]:
            print(f"Recreating collection with correct dimensions...")
            client.delete_collection(collection_name)
            client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=config["embedding_dimension"], distance=Distance.COSINE)
            )
            print(f"Created collection: {collection_name}")
    except Exception:
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=config["embedding_dimension"], distance=Distance.COSINE)
        )
        print(f"Created collection: {collection_name}")


def should_ignore_file(file_path, ignore_patterns):
    """Check if a file should be ignored based on .cocoignore patterns"""
    # Convert to relative path from project root and normalize path separators
    rel_path = str(file_path).replace('\\', '/')
    rel_path = rel_path.replace('//', '/')  # Remove double slashes

    for pattern in ignore_patterns:
        # Normalize pattern path separators
        normalized_pattern = pattern.replace('\\', '/')

        # Handle negation patterns (starting with !)
        if normalized_pattern.startswith('!'):
            # If file matches negation pattern, it should NOT be ignored
            neg_pattern = normalized_pattern[1:]
            if fnmatch.fnmatch(rel_path, neg_pattern):
                return False
            # Also check if any parent directory matches negation pattern
            if neg_pattern.endswith('/'):
                if any(fnmatch.fnmatch(part, neg_pattern.rstrip('/')) for part in rel_path.split('/')):
                    return False
        else:
            # Handle directory patterns (ending with /)
            if normalized_pattern.endswith('/'):
                if rel_path.startswith(normalized_pattern):
                    return True
            # Handle file patterns
            elif fnmatch.fnmatch(rel_path, normalized_pattern):
                return True
            # Handle glob patterns that might match subdirectories
            elif '*' in normalized_pattern:
                if fnmatch.fnmatch(rel_path, normalized_pattern):
                    return True

    return False


@cocoindex.transform_flow()
def text_to_embedding(
    text: cocoindex.DataSlice[str],
) -> cocoindex.DataSlice[list[float]]:
    """
    Embed the text using Ollama model through CocoIndex.
    This is a shared logic between indexing and querying, so extract it as a function.
    """
    return text.transform(
        cocoindex.functions.EmbedText(
            api_type=cocoindex.LlmApiType.OLLAMA,
            model=config["ollama_model"],
            address=config["ollama_url"],
            output_dimension=config["embedding_dimension"],
        )
    )


def text_embedding_flow_impl(
    flow_builder: cocoindex.FlowBuilder, data_scope: cocoindex.DataScope
) -> None:
    """
    Define a flow that embeds text into a vector database using Ollama embeddings and Chonkie chunking.
    """
    # Load .cocoignore patterns for filtering
    ignore_patterns = load_cocoignore_patterns()

    # Convert supported extensions to included patterns
    # Use globset syntax: ** is required to match nested directories.
    included_patterns = [f"**/*{ext}" for ext in config["supported_extensions"]]

    # Add local file source with built-in filtering
    data_scope["documents"] = flow_builder.add_source(
        cocoindex.sources.LocalFile(
            path=config["docs_directory"],
            included_patterns=included_patterns,
            excluded_patterns=ignore_patterns if ignore_patterns else None
        )
    )

    doc_embeddings = data_scope.add_collector()

    with data_scope["documents"].row() as doc:
        doc["chunks"] = doc["content"].transform(
            cocoindex.functions.SplitRecursively(),
            language="markdown",
            chunk_size=config["chunk_size"],
            chunk_overlap=config["chunk_overlap"],
        )

        with doc["chunks"].row() as chunk:
            chunk["embedding"] = text_to_embedding(chunk["text"])
            doc_embeddings.collect(
                id=cocoindex.GeneratedField.UUID,
                filename=doc["filename"],
                location=chunk["location"],
                text=chunk["text"],
                # 'text_embedding' is the name of the vector we've created the Qdrant collection with.
                text_embedding=chunk["embedding"],
            )

    doc_embeddings.export(
        "doc_embeddings",
        cocoindex.targets.Qdrant(
            collection_name=config["qdrant_collection"]
        ),
        primary_key_fields=["id"],
        vector_indexes=[
            cocoindex.VectorIndexDef(
                field_name="text_embedding",
                metric=cocoindex.VectorSimilarityMetric.COSINE_SIMILARITY
            )
        ]
    )


@functools.cache
def get_qdrant_client() -> QdrantClient:
    return QdrantClient(url=config["qdrant_url"], prefer_grpc=True)


def validate_docs_directory(docs_path: str = config["docs_directory"]) -> Optional[Path]:
    """Validate and return the docs directory path."""
    if not os.path.exists(docs_path):
        print(f"Error: '{docs_path}' directory not found!")
        print("Please create a 'docs' directory with the documents you want to index.")
        return None

    docs_dir = Path(docs_path)
    file_count = len([f for f in docs_dir.rglob('*') if f.is_file()])
    print(f"Found '{docs_path}' directory with {file_count} files")
    return docs_dir


def print_startup_info(ignore_patterns: List[str]) -> None:
    """Print startup information and instructions."""
    print("\nRunning CocoIndex indexing flow...")
    print("   This will:")
    print("   1. Process documents from the docs/ directory")
    print("   2. Chunk text using Chonkie library")
    print("   3. Generate embeddings using Ollama")
    print("   4. Store results in Qdrant vector database")

    if ignore_patterns:
        print(f"   Loaded {len(ignore_patterns)} ignore patterns from .cocoignore")
    else:
        print("   No .cocoignore patterns found")


def _main() -> None:
    """
    Main function to run the CocoIndex flow for all documents in the docs/ directory.
    This processes documents, generates embeddings using Ollama, chunks using Chonkie,
    and stores them in Qdrant using the CocoIndex framework.
    """
    print("Starting document indexing process...")
    print("=" * 50)

    try:
        # Validate docs directory
        docs_dir = validate_docs_directory()
        if not docs_dir:
            return

        # Load .cocoignore patterns
        ignore_patterns = load_cocoignore_patterns()

        # Print startup information
        print_startup_info(ignore_patterns)

        print("\nRunning CocoIndex flow with:")
        print("   - Ollama embeddings")
        print("   - Chonkie chunking")
        print("   - Qdrant vector database")
        if ignore_patterns:
            print(f"   - {len(ignore_patterns)} .cocoignore patterns applied")

        print("\nProcessing documents through CocoIndex flow...")

        # Create the flow
        text_embedding_flow = cocoindex.open_flow("TextEmbeddingWithQdrantMain", text_embedding_flow_impl)

        # Add search handler
        @text_embedding_flow.query_handler(
            result_fields=cocoindex.QueryHandlerResultFields(
                embedding=["embedding"],
                score="score",
            ),
        )
        def search(query: str) -> cocoindex.QueryOutput:
            client = get_qdrant_client()

            # Get the embedding for the query using our transform flow
            try:
                query_embedding = text_to_embedding.eval(query)
            except Exception as e:
                print(f"Error during search: {e}")
                raise

            search_results = client.search(
                collection_name=config["qdrant_collection"],
                query_vector=("text_embedding", query_embedding),
                limit=config["search_limit"],
            )
            return cocoindex.QueryOutput(
                results=[
                    {
                        "filename": result.payload["filename"],
                        "text": result.payload["text"],
                        "embedding": result.vector,
                        "score": result.score,
                    }
                    for result in search_results
                ],
                query_info=cocoindex.QueryInfo(
                    embedding=query_embedding,
                    similarity_metric=cocoindex.VectorSimilarityMetric.COSINE_SIMILARITY,
                ),
            )

        # Setup the flow
        text_embedding_flow.setup(report_to_stdout=True)

        # Trigger an update to process any new documents
        text_embedding_flow.update()

        print("\nIndexing completed successfully!")
        print("Your documents are now indexed and ready for semantic search!")
        print("   You can now start the MCP server: uv run python -m src.mcp_server.server")

    except Exception as e:
        print(f"\nError during indexing: {e}")
        print("\nTroubleshooting tips:")
        print("   1. Make sure Qdrant is running: docker run -d -p 6334:6334 -p 6333:6333 qdrant/qdrant")
        print(f"   2. Make sure Ollama is running with the embedding model:")
        print(f"      ollama pull {config['ollama_model']}")
        print("   3. Check your .env configuration")
        print("   4. Ensure your .cocoignore patterns are valid")
        return


if __name__ == "__main__":
    load_dotenv()
    # Initialize CocoIndex with default settings
    cocoindex.init()
    _main()
