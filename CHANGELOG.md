# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-03-25

### Added
- **Architectural Analysis**: New `insight architecture` command for pattern detection.
- **Project Stories**: Cinematic `insight stories` command for 8-chapter codebase narratives.
- **Phased Streaming**: Real-time token delivery with `[PHASE 0-4]` status indicators.
- **AST-Based Chunking**: Precise logic-aware code splitting for high-fidelity retrieval.
- **Code Graph Engine**: Dependency tracking and multi-file relationship resolution.
- **Security & Ethics**: Strict `ANTI-HALLUCINATION MANDATE` and refusal logic for out-of-scope queries.

### Changed
- Refactored repository scanner to use `Path.rglob` for brute-force reliability.
- Optimized `ConversationalRetrievalChain` to bypass buffering and support direct LLM streaming.
- Standardized default LLM to `qwen2.5-coder:latest` (7B) for local reasoning.

### Fixed
- Resolved file discovery issues where hidden or nested directories were skipped.
- Eliminated common hallucinations in authentication and orchestration queries.
