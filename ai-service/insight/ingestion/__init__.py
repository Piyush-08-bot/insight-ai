"""Document ingestion module for INsight."""

from insight.ingestion.loader import load_codebase, CodebaseIngestor
from insight.ingestion.parser import PythonParser, CodeMetadata, CodeDocument

__all__ = [
    "load_codebase",
    "CodebaseIngestor",
    "PythonParser",
    "CodeMetadata",
    "CodeDocument",
]
