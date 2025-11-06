#!/usr/bin/env python3
"""
Utility to force reindexing by clearing CocoIndex state.
"""

import sys
import os
from pathlib import Path

# Add src to path to import our modules
sys.path.insert(0, str(Path(__file__).parent.parent))

import cocoindex
from ..config import config
from .main_flow import text_embedding_flow_impl, get_qdrant_client, text_to_embedding

def force_reindex():
    """Force reindexing by clearing CocoIndex state and re-running update."""
    print("Forcing reindexing of all documents...")
    print("=" * 50)

    try:
        # Initialize CocoIndex
        cocoindex.init()

        # Clear all existing CocoIndex state to force reprocessing
        print("Clearing existing CocoIndex state...")
        cocoindex.drop_all_flows()

        # Open the flow
        text_embedding_flow = cocoindex.open_flow("TextEmbeddingWithQdrantMain", text_embedding_flow_impl)

        # Add search handler (from main_flow.py)
        @text_embedding_flow.query_handler(
            result_fields=cocoindex.QueryHandlerResultFields(
                embedding=["embedding"],
                score="score",
            ),
        )
        def search(query: str) -> cocoindex.QueryOutput:
            from qdrant_client.models import Filter

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
        print("Setting up CocoIndex flow...")
        text_embedding_flow.setup(report_to_stdout=True)

        # Force update (this will process all files regardless of state)
        print("\nForcing full reindex of all documents...")
        stats = text_embedding_flow.update()
        print(f"Update statistics: {stats}")

        print("\nForce reindexing completed successfully!")
        print("All documents have been reprocessed and indexed.")

    except Exception as e:
        print(f"\nError during force reindexing: {e}")
        return 1

    return 0

if __name__ == "__main__":
    exit(force_reindex())