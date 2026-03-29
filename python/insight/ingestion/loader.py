"""
Document Ingestion for INsight.

Provides both a simple load_codebase() function and a full-featured
CodebaseIngestor class with AST parsing and metadata extraction.
"""

import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

from langchain_core.documents import Document

from insight.ingestion.parser import (
    PythonParser, JavaScriptParser, CodeMetadata, CodeDocument
)
from insight.vectorstore.graph_manager import GraphManager


# ─── File type to parser mapping ────────────────────────────────────
PARSERS = {
    '.py': PythonParser,
    '.js': JavaScriptParser,
    '.jsx': JavaScriptParser,
    '.ts': JavaScriptParser,
    '.tsx': JavaScriptParser,
}

DEFAULT_EXCLUDE_DIRS = [
    'venv', 'env', '.venv', '__pycache__', '.git',
    'node_modules', 'dist', 'build', '.next',
    'coverage', '.pytest_cache', '.mypy_cache',
    '.egg-info', '.tox', 'chroma_db', 'faiss_index',
]

DEFAULT_EXTENSIONS = ['.py', '.js', '.ts', '.jsx', '.tsx', '.md', '.json']


class CodebaseIngestor:
    """
    Full-featured codebase ingestor with AST parsing.

    Scans project directories, parses code, extracts metadata,
    and creates structured documents for the RAG pipeline.
    """

    def __init__(
        self,
        project_path: str,
        exclude_dirs: Optional[List[str]] = None,
        include_extensions: Optional[List[str]] = None
    ):
        self.project_path = Path(project_path).resolve()
        self.exclude_dirs = exclude_dirs or DEFAULT_EXCLUDE_DIRS
        self.include_extensions = include_extensions or DEFAULT_EXTENSIONS
        self.documents: List[CodeDocument] = []
        self.graph_manager = GraphManager(persist_path=str(self.project_path / "code_graph.json"))

    def scan_files(self) -> List[Path]:
        """Scan project directory for code files using robust recursive glob."""
        files = []
        exclude_dirs_set = set(self.exclude_dirs)
        
        # Brute force search for all files with correct extensions
        for ext in self.include_extensions:
            # rglob is generally very robust on Mac/UNIX
            for p in self.project_path.rglob(f"*{ext}"):
                # Manual exclusion check on the full pathparts to be extra safe
                if any(ex in p.parts for ex in exclude_dirs_set):
                    continue
                files.append(p)
        
        return sorted(list(set(files)))

    def ingest(self) -> List[CodeDocument]:
        """Run complete ingestion pipeline."""
        files = self.scan_files()

        if not files:
            print("❌ No files found!")
            return []

        print(f"📄 Processing {len(files)} files: {[f.name for i, f in enumerate(list(files)) if i < 10]}...")

        for file_path in files:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()

                # Skip empty files
                if not content.strip():
                    continue

                # Parse with appropriate parser
                parser_cls = PARSERS.get(file_path.suffix)
                if parser_cls:
                    metadata = parser_cls.parse(file_path, content)
                else:
                    metadata = CodeMetadata(
                        functions=[], classes=[], imports=[], calls=[],
                        docstring=None,
                        language=file_path.suffix.lstrip('.') if file_path.suffix else 'unknown',
                        file_path=str(file_path),
                        file_size=len(content),
                        line_count=content.count('\n') + 1
                    )

                doc = CodeDocument(content=content, metadata=metadata)
                self.documents.append(doc)

                # NEW: Add to graph
                rel_path = str(file_path.relative_to(self.project_path))
                self.graph_manager.add_file_node(rel_path, metadata.__dict__)

            except Exception as e:
                print(f"⚠️  Skipping {file_path.name}: {e}")
                continue

        # Resolve edges and save
        self.graph_manager.resolve_edges()
        self.graph_manager.save()

        print(f"✅ Ingested {len(self.documents)} documents and built code graph")
        return self.documents

    def to_langchain_documents(self) -> List[Document]:
        """Convert CodeDocuments to LangChain Documents with rich metadata."""
        lc_docs = []
        for doc in self.documents:
            try:
                rel_path = Path(doc.metadata.file_path).relative_to(self.project_path)
            except ValueError:
                rel_path = Path(doc.metadata.file_path).name

            functions_list = [f['name'] for f in doc.metadata.functions]
            classes_list = [c['name'] for c in doc.metadata.classes]
            imports_list = doc.metadata.imports
            calls_list = doc.metadata.calls

            metadata = {
                'source': str(rel_path),
                'language': doc.metadata.language,
                'size': doc.metadata.file_size,
                'lines': doc.metadata.line_count,
                'complexity': doc.metadata.complexity,
                'functions': ", ".join(functions_list) if functions_list else "none",
                'classes': ", ".join(classes_list) if classes_list else "none",
                'imports': ", ".join(imports_list) if imports_list else "none",
                'calls': ", ".join(calls_list) if calls_list else "none",
                'num_functions': len(functions_list),
                'num_classes': len(classes_list),
                'num_imports': len(imports_list),
                'num_calls': len(calls_list),
            }
            lc_docs.append(Document(page_content=doc.content, metadata=metadata))

        return lc_docs

    def get_stats(self) -> Dict[str, Any]:
        """Get ingestion statistics."""
        if not self.documents:
            return {}

        total_lines = sum(d.metadata.line_count for d in self.documents)
        total_size = sum(d.metadata.file_size for d in self.documents)
        total_functions = sum(len(d.metadata.functions) for d in self.documents)
        total_classes = sum(len(d.metadata.classes) for d in self.documents)

        languages = {}
        for doc in self.documents:
            lang = doc.metadata.language
            languages[lang] = languages.get(lang, 0) + 1

        return {
            "total_files": len(self.documents),
            "total_lines": total_lines,
            "total_size_kb": round(total_size / 1024, 1),
            "total_functions": total_functions,
            "total_classes": total_classes,
            "languages": languages,
        }


def load_codebase(
    project_path: str,
    file_types: Optional[List[str]] = None
) -> List[Document]:
    """
    Simple function to load a codebase into LangChain Documents.

    This is the easy-to-use wrapper around CodebaseIngestor.

    Args:
        project_path: Path to the project directory
        file_types: File extensions to load (e.g. ['.py', '.js'])

    Returns:
        List of LangChain Document objects with metadata
    """
    ingestor = CodebaseIngestor(
        project_path=project_path,
        include_extensions=file_types or DEFAULT_EXTENSIONS
    )
    ingestor.ingest()
    return ingestor.to_langchain_documents()
