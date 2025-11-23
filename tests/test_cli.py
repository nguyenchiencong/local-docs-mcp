import json

import src.cli as cli
from src.search.models import SearchResult


class FakeSearchService:
    def __init__(self):
        self.calls = {}

    def semantic_search(self, query, limit=None, min_similarity_score=None):
        self.calls["semantic_search"] = {
            "query": query,
            "limit": limit,
            "min_similarity_score": min_similarity_score,
        }
        return [
            SearchResult(
                id="doc-1",
                filename="file1.md",
                text="Example text about embeddings and search configuration.",
                score=0.91,
                embedding=[],
                location=10,
            )
        ]

    def hybrid_search(self, query, semantic_weight=None, limit=None, min_similarity_score=None):
        self.calls["hybrid_search"] = {
            "query": query,
            "semantic_weight": semantic_weight,
            "limit": limit,
            "min_similarity_score": min_similarity_score,
        }
        return []

    def document_retrieval(self, document_id):
        self.calls["document_retrieval"] = {"document_id": document_id}
        return {
            "id": document_id,
            "filename": "file1.md",
            "text": "Document content",
            "location": 5,
        }

    def search_with_metadata_filter(self, query, metadata_filter, limit=None, min_similarity_score=None):
        self.calls["search_with_metadata_filter"] = {
            "query": query,
            "metadata_filter": metadata_filter,
            "limit": limit,
            "min_similarity_score": min_similarity_score,
        }
        return []

    def get_collection_info(self):
        self.calls["get_collection_info"] = {}
        return {
            "name": "local-docs-collection",
            "points_count": 42,
            "status": "green",
        }


def test_semantic_search_cli_pretty_output(monkeypatch, capsys):
    service = FakeSearchService()
    monkeypatch.setattr(cli, "build_search_service", lambda overrides=None: service)

    exit_code = cli.main(["semantic_search", "--query", "embeddings", "--limit", "2"])
    out = capsys.readouterr().out

    assert exit_code == 0
    assert "semantic_search results for query: embeddings" in out
    assert "doc-1" in out
    assert "file1.md" in out
    assert service.calls["semantic_search"]["limit"] == 2


def test_get_collection_info_json(monkeypatch, capsys):
    service = FakeSearchService()
    monkeypatch.setattr(cli, "build_search_service", lambda overrides=None: service)

    exit_code = cli.main(["get_collection_info", "--json"])
    out = capsys.readouterr().out
    parsed = json.loads(out)

    assert exit_code == 0
    assert parsed["name"] == "local-docs-collection"
    assert "points_count" in parsed
    assert "get_collection_info" in service.calls
