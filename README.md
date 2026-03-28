# ✨ INsight AI

> **Your codebase, understood.** An advanced intelligence engine for developers, right in your terminal.

INsight is a free, AI-powered codebase analysis tool. It uses Retrieval-Augmented Generation (RAG) to help you understand, debug, and learn about any codebase—running completely locally on your machine for 100% privacy and zero cost.

---

## 🚀 Key Features

- **🧠 Local Intelligence**: Powered by `qwen2.5-coder` (via Ollama) for GPT-4 level coding reasoning.
- **📁 Semantic Analysis**: Specialized chains for **Overview**, **Architecture**, **Dependencies**, and **Learning Paths**.
- **💬 Interactive Chat**: Chat with your code with full conversation memory.
- **📄 Exportable Stories**: Generate full codebase reports as `.md` documents.
- **🌈 Premium CLI UI**: Beautiful, professional terminal output with visual project trees and progress indicators.
- **🔒 Privacy First**: No code leaves your machine. Local embeddings + local LLM.

---

## 🛠️ Quick Start

### 1. Install
Install the CLI tool globally:
```bash
npm install -g insight-ai
```

### 2. Setup (Ollama Required for Free AI)
If you don't have Ollama, download it at [ollama.com](https://ollama.com).
```bash
# Pull the recommended free coding model
ollama pull qwen2.5-coder

# Run the project setup
insight setup
```

### 3. Analyze & Chat
```bash
# Index your project
insight analyze ./path/to/your/code

# Start chatting
insight chat
```

---

## 📖 CLI Commands

| Command | Description |
| :--- | :--- |
| `insight analyze <path>` | Index a codebase for the AI to understand. |
| `insight chat` | Interactive Q&A about your code. |
| `insight overview` | High-level summary of the project structure. |
| `insight architecture` | Analyze design patterns and layers. |
| `insight deps` | Map out internal and external dependencies. |
| `insight learn` | Create a step-by-step onboarding guide. |
| `insight report -o <file>` | Generate a master AI report as a file. |
| `insight doctor` | Check system health (Python, Ollama, Vector DB). |

---

## 🛠️ Technical Info

- **Engine**: Python (LangChain, ChromaDB, Sentence-Transformers)
- **Wrapper**: Node.js (npm global package)
- **LLM**: Ollama (default) or OpenAI (optional)
- **Embeddings**: Local HuggingFace (default)

---

Developed with ❤️ for developers who love staying in the terminal.
