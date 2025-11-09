# Changelog

All notable changes to this project will be documented in this file.

## 2025-11-09

- Load `.env` automatically during config bootstrap and normalize both the docs directory and `.cocoignore` paths so CocoIndex workers always see the right files.
- Updated the CocoIndex LocalFile source to use recursive glob patterns (`**/*.ext`) ensuring nested documentation is indexed consistently, and tightened `force_reindex` to drop only the target flow before rebuilding.
- Added a tracked `.cocoignore.example`, ignored real `.cocoignore`, and documented the copy step so contributors can customize local filters without affecting version control.
- Added config-driven chunk sizing and overlap controls exposed via `[tool.local-docs]` plus env overrides.
- Enhanced hybrid search with phrase/filename keyword boosts, tunable semantic weighting, and an MMR re-ranking pass.
- Introduced configurable Qdrant HNSW `ef` parameter and default similarity threshold for better recall control.
- Updated README with a "Recent Improvements" section summarizing these search/indexing upgrades.
