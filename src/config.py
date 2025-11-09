"""Simple configuration loader for local-docs-mcp project."""

import os
from pathlib import Path

from dotenv import load_dotenv


def load_config():
    """Load configuration from pyproject.toml with simple fallbacks."""
    project_root = Path(__file__).parent.parent
    config_path = project_root / "pyproject.toml"

    # Load environment variables from .env if present
    load_dotenv(project_root / ".env", override=False)

    # Default configuration
    config = {
        "qdrant_url": "http://localhost:6334",
        "qdrant_collection": "local-docs-collection",
        "ollama_url": "http://localhost:11434",
        "ollama_model": "hf.co/Qwen/Qwen3-Embedding-0.6B-GGUF:F16",
        "docs_directory": "docs",
        "cocoignore_file": ".cocoignore",
        "supported_extensions": [".md", ".rst", ".txt"],
        "embedding_dimension": 1024,
        "search_limit": 10,
        "similarity_threshold": 0.15,
        "search_hnsw_ef": 256,
        "chunk_size": 1200,
        "chunk_overlap": 200,
        "hybrid_semantic_weight": 0.85,
        "mmr_lambda": 0.75,
    }

    # Load from pyproject.toml if it exists
    if config_path.exists():
        try:
            import toml
            with open(config_path, 'r', encoding='utf-8') as f:
                full_config = toml.load(f)
                project_config = full_config.get("tool", {}).get("local-docs", {})
                config.update(project_config)
        except ImportError:
            # toml not available, use defaults
            pass
        except Exception:
            # Error reading config, use defaults
            pass

    # Override with environment variables
    env_mappings = {
        "LOCAL_DOCS_QDRANT_URL": "qdrant_url",
        "LOCAL_DOCS_QDRANT_COLLECTION": "qdrant_collection",
        "LOCAL_DOCS_OLLAMA_URL": "ollama_url",
        "LOCAL_DOCS_OLLAMA_MODEL": "ollama_model",
        "LOCAL_DOCS_DOCS_DIRECTORY": "docs_directory",
        "LOCAL_DOCS_EMBEDDING_DIMENSION": "embedding_dimension",
        "LOCAL_DOCS_SEARCH_LIMIT": "search_limit",
        "LOCAL_DOCS_SIMILARITY_THRESHOLD": "similarity_threshold",
        "LOCAL_DOCS_SEARCH_HNSW_EF": "search_hnsw_ef",
        "LOCAL_DOCS_CHUNK_SIZE": "chunk_size",
        "LOCAL_DOCS_CHUNK_OVERLAP": "chunk_overlap",
        "LOCAL_DOCS_HYBRID_WEIGHT": "hybrid_semantic_weight",
        "LOCAL_DOCS_MMR_LAMBDA": "mmr_lambda",
    }

    for env_var, config_key in env_mappings.items():
        if env_var in os.environ:
            value = os.environ[env_var]
            if config_key in [
                "embedding_dimension",
                "search_limit",
                "chunk_size",
                "chunk_overlap",
                "search_hnsw_ef",
            ]:
                value = int(value)
            elif config_key in ["similarity_threshold", "hybrid_semantic_weight", "mmr_lambda"]:
                value = float(value)
            config[config_key] = value

    # Convert supported_extensions to frozenset
    if isinstance(config["supported_extensions"], list):
        config["supported_extensions"] = frozenset(config["supported_extensions"])

    # Ensure docs_directory is absolute so cocoindex worker resolves it correctly
    docs_dir = Path(config["docs_directory"])
    if not docs_dir.is_absolute():
        docs_dir = (project_root / docs_dir).resolve()
    else:
        docs_dir = docs_dir.resolve()
    config["docs_directory"] = docs_dir.as_posix()

    # Normalize cocoignore path relative to project root if needed
    cocoignore_path = Path(config["cocoignore_file"])
    if not cocoignore_path.is_absolute():
        cocoignore_path = (project_root / cocoignore_path).resolve()
    else:
        cocoignore_path = cocoignore_path.resolve()
    config["cocoignore_file"] = cocoignore_path.as_posix()

    return config


# Load configuration once
config = load_config()
