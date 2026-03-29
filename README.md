# 🔍 INsight-AI

**The Professional AI Code Analyst for your Terminal.**

Analyze, understand, and chat with any codebase in seconds. INsight uses advanced RAG (Retrieval-Augmented Generation) to give you deep architectural insights, dependency maps, and a conversational interface for your code.

---

## ✨ Features

- **🌐 Pro Cloud Storage**: Persistent memory backed by **Supabase**. Your chat history and workspaces follow you anywhere.
- **🔑 Global Config Manager**: Set your API keys once (`insight config set-key`) and use them across any project.
- **🧠 Intelligent RAG**: Uses tree-sitter based chunking to understand code structure (Classes, Functions, Imports) better than standard text splitters.
- **🆓 100% Local Option**: Supports **Ollama** for free, private, local analysis.
- **⚡ Remote Knowledge Base**: Connects to remote **ChromaDB** servers for centralized team knowledge.

---

## 🚀 Quick Start

### 1. Install
```bash
npm install -g insight-ai
```

### 2. Configure (Choose your AI)

**Option A: Cloud AI (Fastest & Most Accurate)**
Save your keys globally to use them across any project. Supported providers: `openai`, `groq`, `anthropic`, `google`.

```bash
# OpenAI (Default)
insight config set-key openai sk-proj-123...

# Groq (Extreme Speed)
insight config set-key groq gsk_456...

# Anthropic (Deep Reasoning)
insight config set-key anthropic sk-ant-789...

# Google Gemini
insight config set-key google AIzaSy012...
```

**Option B: 100% Local AI (Free & Private)**
If you don't have an API key, you can run the AI directly on your computer:
1. Install [Ollama](https://ollama.com).
2. Download the recommended code model by running:
   ```bash
   ollama run qwen2.5-coder
   ```
3. Run INsight with the local provider flags:
   ```bash
   # Analyze with local model
   insight analyze . --embedding ollama

   # Chat with local model
   insight chat --provider ollama --model qwen2.5-coder
   ```

### 3. Analyze
Go to your project folder and run:
```bash
insight analyze .
```

### 4. Chat & Explore
```bash
# Open interactive chat
insight chat

# Generate a learning path for the repo
insight learn

# Map code architecture
insight architecture
```

---

## 🛠 Commands

| Command | Description |
|---------|-------------|
| `insight analyze [path]` | Index and analyze code structure |
| `insight chat` | Interactive AI chat with code context |
| `insight config` | Manage global API keys and settings |
| `insight learn` | Generate a roadmap to learn the codebase |
| `insight architecture` | Map high-level class and module relationships |
| `insight report` | Generate a comprehensive PDF/MD report |
| `insight setup` | Repair or reinstall Python dependencies |

---

## ⚙️ How it Works

1. **Ingest**: Scans your files and builds a metadata code graph.
2. **Embed**: Converts code into semantic vectors (ChromaDB).
3. **Persist**: Saves your sessions and preferences to the cloud (Supabase).
4. **Reason**: Uses LLMs (GPT-4, Claude, or local Llama) to answer complex queries.

---

## 📋 Requirements

- **Node.js**: 18+
- **Python**: 3.9+ (Installed automatically via `postinstall`)
- **Ollama**: (Optional) For free local AI analysis.

---

**License**: MIT  
**Author**: Piyush Raj  
**Repository**: [github.com/Piyush-08-bot/insight-ai](https://github.com/Piyush-08-bot/insight-ai)
