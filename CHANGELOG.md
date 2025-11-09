# Changelog

All notable changes to this project will be documented in this file.

## 2024-10-29

- Added config-driven chunk sizing and overlap controls exposed via `[tool.local-docs]` plus env overrides.
- Enhanced hybrid search with phrase/filename keyword boosts, tunable semantic weighting, and an MMR re-ranking pass.
- Introduced configurable Qdrant HNSW `ef` parameter and default similarity threshold for better recall control.
- Updated README with a “Recent Improvements” section summarizing these search/indexing upgrades.
