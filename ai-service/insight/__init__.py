"""INsight - AI-Powered Code Understanding Tool."""

import os
import warnings
import logging

# 1. Silence Python Warnings (Pydantic v1, LangChain Deprecations, etc.)
warnings.filterwarnings("ignore", category=UserWarning, module="pydantic")
warnings.filterwarnings("ignore", category=DeprecationWarning)
# Try to catch LangChain-specific deprecation warnings which often use custom categories
try:
    from langchain_core._api.deprecation import LangChainDeprecationWarning
    warnings.filterwarnings("ignore", category=LangChainDeprecationWarning)
except ImportError:
    pass

# 2. Silence Third-Party Loggers
for logger_name in ["transformers", "huggingface_hub", "absl", "urllib3", "chromadb"]:
    logging.getLogger(logger_name).setLevel(logging.ERROR)

# 3. Environment Variable Suppressions
os.environ["TRANSFORMERS_VERBOSITY"] = "error"
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
# Disable unauthenticated request warnings if possible
os.environ["HTTP_LOG_LEVEL"] = "error" 

__version__ = "0.1.0"

from insight.ingestion import load_codebase, CodebaseIngestor
from insight.vectorstore import create_vector_store, load_vector_store, VectorStoreManager
from insight.chains import create_qa_chain, chat, run_analysis, run_full_report
from insight.chunking import CodeChunker, ChunkingConfig

__all__ = [
    "load_codebase",
    "CodebaseIngestor",
    "create_vector_store",
    "load_vector_store",
    "VectorStoreManager",
    "create_qa_chain",
    "chat",
    "run_analysis",
    "run_full_report",
    "CodeChunker",
    "ChunkingConfig",
]
