# INsight AI Service

Clean, organized structure for the RAG-powered code understanding system.

## 📁 Project Structure

```
ai-service/
├── core/                    # Core modules
│   ├── ingestion_pipeline.py   # Code scanning & parsing
│   ├── chunking.py              # Text splitting
│   ├── vectorstore.py           # Embeddings & search
│   └── rag_pipeline.py          # Main orchestrator
│
├── tests/                   # Test scripts
│   ├── simple_test.py
│   ├── test_ingestion.py
│   └── test_rag_pipeline.py
│
├── tools/                   # Utility scripts
│   └── view_chroma.py          # Database viewer
│
├── docs/                    # Documentation
│   ├── README_QUICK.md
│   ├── PROJECT_ROADMAP.md
│   └── INGESTION_GUIDE.md
│
├── data/                    # Generated data
│   └── ingestion_results.json
│
├── chroma_db/              # Vector database
│   └── chroma.sqlite3
│
├── .env                    # API keys (add yours!)
├── requirements.txt        # Dependencies
└── README.md              # This file
```

## 🚀 Quick Start

### 1. Install
```bash
pip install -r requirements.txt
```

### 2. Configure
Add your OpenAI API key to `.env`:
```bash
OPENAI_API_KEY=sk-proj-your-key-here
```

### 3. Run
```bash
# Index your codebase
python3 core/rag_pipeline.py ../backend --force

# Query it
python3 core/rag_pipeline.py ../backend -q "how does auth work?"

# View database
python3 tools/view_chroma.py
```

## 📊 What's Inside

**Core Modules:**
- `ingestion_pipeline.py` - Scans code, extracts metadata
- `chunking.py` - Splits code into optimal chunks
- `vectorstore.py` - Manages embeddings & search
- `rag_pipeline.py` - Main entry point

**Tools:**
- `view_chroma.py` - View vector database contents

**Tests:**
- `simple_test.py` - Quick validation
- `test_ingestion.py` - Test code scanning
- `test_rag_pipeline.py` - End-to-end test

## 📚 Documentation

- **Quick Start:** `docs/README_QUICK.md`
- **Full Roadmap:** `docs/PROJECT_ROADMAP.md`
- **Ingestion Guide:** `docs/INGESTION_GUIDE.md`

## 🎯 Current Status

- ✅ Phase 1: Vector Store (COMPLETE)
- ⏭️ Phase 2: Q&A with GPT-4 (NEXT)
- 🔜 Phase 3: Conversational Interface
- 📅 Phase 4: Web App

See `docs/PROJECT_ROADMAP.md` for details!
