# 🔍 INsight - AI-Powered Code Understanding Tool

> Analyze any codebase with AI. Get overviews, learning paths, architecture analysis, and chat with your code. **100% free with Ollama.**

## Install

```bash
npm install -g insight-ai
```

## Quick Start

```bash
# 1. Setup (first time only)
insight setup

# 2. Install free AI model (first time only)
ollama pull qwen2.5-coder

# 3. Analyze your project
insight analyze ./my-project

# 4. Chat with your code!
insight chat
```

## Commands

| Command | Description |
|---------|-------------|
| `insight analyze <path>` | Analyze a codebase |
| `insight chat` | Chat with your code (with memory) |
| `insight overview [path]` | Project overview |
| `insight learn [path]` | Learning path for the codebase |
| `insight architecture [path]` | Architecture analysis |
| `insight deps [path]` | Dependency mapping |
| `insight report [path]` | Full report (all analysis types) |
| `insight doctor` | Check system health |
| `insight setup` | Install/repair dependencies |

## Options

```bash
-p, --provider    LLM provider: ollama (free) or openai (paid)
-m, --model       Model name override
-d, --persist-dir Vector store directory
-f, --file-types  File types to analyze
-e, --embedding   Embedding: local (free) or openai (paid)
-o, --output      Save report to file
```

## Requirements

- **Node.js** 16+
- **Python** 3.9+
- **Ollama** (free, local AI) — [Download](https://ollama.com/download)

## How It Works

INsight uses a RAG (Retrieval Augmented Generation) pipeline:

1. **Ingest** — Scans your code files, extracts metadata (functions, classes, imports)
2. **Chunk** — Splits code into language-aware chunks (Python, JS/TS, Markdown)
3. **Embed** — Creates vector embeddings (local, free — no API key needed)
4. **Index** — Stores embeddings in Chroma vector database
5. **Query** — Uses Ollama LLM to answer questions with code context

Built with: LangChain · Ollama · ChromaDB · HuggingFace Embeddings

## License

MIT
