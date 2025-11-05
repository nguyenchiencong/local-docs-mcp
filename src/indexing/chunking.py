"""
Text chunking utilities for document processing.

This module provides chunking functionality using Chonkie with TikToken
for optimal text segmentation before embedding generation.
"""

from typing import List, Dict
from chonkie import TokenChunker
import tiktoken


def chunk_with_chonkie(text: str) -> List[Dict]:
    """
    Chunk text using chonkie TokenChunker with tiktoken.

    Args:
        text: The input text to chunk

    Returns:
        List of dictionaries containing chunk information including:
        - text: The chunk text
        - location: Chunk index
        - token_count: Number of tokens in the chunk
        - start_index: Start position in original text
        - end_index: End position in original text
    """
    # Using TikToken with a specific model encoding
    tokenizer = tiktoken.get_encoding("cl100k_base")

    chunker = TokenChunker(
        tokenizer=tokenizer,
        chunk_size=2000,
        chunk_overlap=500
    )
    chunks = chunker.chunk(text)

    # Convert chonkie chunks to the expected format
    chunk_dicts = []
    for i, chunk in enumerate(chunks):
        chunk_dicts.append({
            "text": chunk.text,
            "location": i,  # Use chunk index as location
            "token_count": chunk.token_count,
            "start_index": chunk.start_index,
            "end_index": chunk.end_index
        })

    return chunk_dicts