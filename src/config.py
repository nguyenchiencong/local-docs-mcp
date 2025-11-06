"""Simple configuration loader for local-docs-mcp project."""

import os
from pathlib import Path


def load_config():
    """Load configuration from pyproject.toml with simple fallbacks."""
    config_path = Path(__file__).parent.parent / "pyproject.toml"

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
    }

    for env_var, config_key in env_mappings.items():
        if env_var in os.environ:
            value = os.environ[env_var]
            if config_key in ["embedding_dimension", "search_limit"]:
                value = int(value)
            config[config_key] = value

    # Convert supported_extensions to frozenset
    if isinstance(config["supported_extensions"], list):
        config["supported_extensions"] = frozenset(config["supported_extensions"])

    return config


# Load configuration once
config = load_config()