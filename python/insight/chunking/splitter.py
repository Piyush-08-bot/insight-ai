"""
Code-Aware Text Chunking for RAG Pipeline.

Language-specific splitting strategies optimized for code:
- Python, JavaScript, TypeScript, Markdown splitters
- Structure-aware splitting (classes, functions, methods)
- Optimal chunk sizes with overlap for context preservation
"""

from typing import List, Dict, Any, Optional
from langchain_text_splitters import RecursiveCharacterTextSplitter, Language
from langchain_core.documents import Document
from dataclasses import dataclass
from enum import Enum


class CodeLanguage(Enum):
    """Supported programming languages for chunking."""
    PYTHON = "python"
    JAVASCRIPT = "js"
    TYPESCRIPT = "ts"
    JAVA = "java"
    GO = "go"
    MARKDOWN = "markdown"
    JSON = "json"
    GENERIC = "generic"


@dataclass
class ChunkingConfig:
    """Configuration for text chunking."""
    chunk_size: int = 1000
    chunk_overlap: int = 200
    add_start_index: bool = True


# Language name normalization map
LANG_MAP = {
    'py': CodeLanguage.PYTHON.value,
    'python': CodeLanguage.PYTHON.value,
    'js': CodeLanguage.JAVASCRIPT.value,
    'javascript': CodeLanguage.JAVASCRIPT.value,
    'ts': CodeLanguage.TYPESCRIPT.value,
    'typescript': CodeLanguage.TYPESCRIPT.value,
    'jsx': CodeLanguage.JAVASCRIPT.value,
    'tsx': CodeLanguage.TYPESCRIPT.value,
    'md': CodeLanguage.MARKDOWN.value,
    'markdown': CodeLanguage.MARKDOWN.value,
    'json': CodeLanguage.JSON.value,
}


class CodeChunker:
    """
    Intelligent code splitter with language-aware strategies.

    Uses LangChain's RecursiveCharacterTextSplitter with
    language-specific separators.
    """

    def __init__(self, config: Optional[ChunkingConfig] = None):
        self.config = config or ChunkingConfig()
        self._splitters = self._init_splitters()

    def _init_splitters(self) -> Dict[str, RecursiveCharacterTextSplitter]:
        """Initialize language-specific text splitters."""
        cfg = self.config
        splitters = {}

        # Python
        splitters[CodeLanguage.PYTHON.value] = RecursiveCharacterTextSplitter.from_language(
            language=Language.PYTHON,
            chunk_size=cfg.chunk_size,
            chunk_overlap=cfg.chunk_overlap,
            add_start_index=cfg.add_start_index
        )

        # JavaScript
        splitters[CodeLanguage.JAVASCRIPT.value] = RecursiveCharacterTextSplitter.from_language(
            language=Language.JS,
            chunk_size=cfg.chunk_size,
            chunk_overlap=cfg.chunk_overlap,
            add_start_index=cfg.add_start_index
        )

        # TypeScript
        splitters[CodeLanguage.TYPESCRIPT.value] = RecursiveCharacterTextSplitter.from_language(
            language=Language.TS,
            chunk_size=cfg.chunk_size,
            chunk_overlap=cfg.chunk_overlap,
            add_start_index=cfg.add_start_index
        )

        # Markdown
        splitters[CodeLanguage.MARKDOWN.value] = RecursiveCharacterTextSplitter.from_language(
            language=Language.MARKDOWN,
            chunk_size=cfg.chunk_size,
            chunk_overlap=cfg.chunk_overlap,
            add_start_index=cfg.add_start_index
        )

        # JSON
        splitters[CodeLanguage.JSON.value] = RecursiveCharacterTextSplitter(
            chunk_size=cfg.chunk_size,
            chunk_overlap=cfg.chunk_overlap,
            separators=["},\n", "}\n", "],\n", "]\n", ",\n", "\n", " "],
            add_start_index=cfg.add_start_index
        )

        # Generic fallback
        splitters[CodeLanguage.GENERIC.value] = RecursiveCharacterTextSplitter(
            chunk_size=cfg.chunk_size,
            chunk_overlap=cfg.chunk_overlap,
            separators=[
                "\n\nclass ", "\n\nfunction ", "\n\ndef ",
                "\n\nasync ", "\n\nconst ", "\n\nlet ",
                "\n\n", "\n", ". ", " ", ""
            ],
            add_start_index=cfg.add_start_index
        )

        return splitters

    def get_splitter(self, language: str) -> RecursiveCharacterTextSplitter:
        """Get appropriate splitter for a language."""
        normalized = LANG_MAP.get(language.lower(), CodeLanguage.GENERIC.value)
        return self._splitters.get(normalized, self._splitters[CodeLanguage.GENERIC.value])

    def chunk_document(self, document: Document) -> List[Document]:
        """Split a single document into chunks with enriched metadata."""
        language = document.metadata.get('language', 'generic')
        splitter = self.get_splitter(language)
        chunks = splitter.split_documents([document])

        for i, chunk in enumerate(chunks):
            chunk.metadata.update({
                'chunk_index': i,
                'total_chunks': len(chunks),
                'chunk_size': len(chunk.page_content),
                'chunked_from': document.metadata.get('source', 'unknown')
            })

        return chunks

    def chunk_documents(self, documents: List[Document]) -> List[Document]:
        """Split multiple documents into chunks."""
        all_chunks = []
        for doc in documents:
            all_chunks.extend(self.chunk_document(doc))
        return all_chunks

    def get_stats(self, documents: List[Document], chunks: List[Document]) -> Dict[str, Any]:
        """Get chunking statistics."""
        if not chunks:
            return {}

        chunk_sizes = [len(c.page_content) for c in chunks]
        total_orig = sum(len(d.page_content) for d in documents) or 1

        return {
            'original_documents': len(documents),
            'total_chunks': len(chunks),
            'avg_chunks_per_doc': round(len(chunks) / max(len(documents), 1), 2),
            'avg_chunk_size': round(sum(chunk_sizes) / len(chunk_sizes)),
            'min_chunk_size': min(chunk_sizes),
            'max_chunk_size': max(chunk_sizes),
        }


import ast
import re

class ASTChunker:
    """
    Function/class-level chunker. One chunk = one complete function or class.
    Falls back to CodeChunker for unsupported languages or parse errors.
    """
    def __init__(self):
        self.char_chunker = CodeChunker()

    def chunk_document(self, document: Document) -> List[Document]:
        lang = document.metadata.get('language', 'generic')
        
        if lang == 'python':
            return self._chunk_python(document)
        elif lang in ('js', 'javascript', 'ts', 'typescript', 'jsx', 'tsx'):
            return self._chunk_js_heuristic(document)
        else:
            # Fallback to existing character splitter for MD, JSON, etc.
            return self.char_chunker.chunk_document(document)

    def _chunk_python(self, document: Document) -> List[Document]:
        try:
            source = document.page_content
            tree = ast.parse(source)
            lines = source.splitlines()
            chunks = []
            
            def process_node(node, parent_name=None):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    start = getattr(node, 'lineno', 1) - 1
                    end = getattr(node, 'end_lineno', start + 1)
                    content = "\n".join([lines[i] for i in range(int(start), int(end))])
                    
                    full_name = f"{parent_name}.{node.name}" if parent_name else node.name
                    chunks.append(Document(
                        page_content=content,
                        metadata={
                            **document.metadata,
                            "type": "function",
                            "name": full_name,
                            "start_line": int(start) + 1,
                            "end_line": int(end)
                        }
                    ))
                elif isinstance(node, ast.ClassDef):
                    # 1. Chunk the class itself (all methods)
                    for item in node.body:
                        process_node(item, parent_name=node.name)
                    
                    # 2. Also add the class itself as a chunk (for high-level summary)
                    start = getattr(node, 'lineno', 1) - 1
                    end = getattr(node, 'end_lineno', start + 1)
                    content = "\n".join([lines[i] for i in range(int(start), int(end))])
                    chunks.append(Document(
                        page_content=content,
                        metadata={
                            **document.metadata,
                            "type": "class",
                            "name": node.name,
                            "start_line": int(start) + 1,
                            "end_line": int(end)
                        }
                    ))

            for node in tree.body:
                process_node(node)
            
            if not chunks:
                return self.char_chunker.chunk_document(document)
                
            return chunks
        except Exception:
            # Safe fallback on parse error
            return self.char_chunker.chunk_document(document)

    def _chunk_js_heuristic(self, document: Document) -> List[Document]:
        """Regex-based heuristic for JS/TS functions since we lack a full parser."""
        source = document.page_content
        # Match function declarations, arrow functions assigned to const, and class definitions
        pattern = re.compile(
            r'((?:export\s+)?(?:async\s+)?function\s*[\w\*]*\s*\([^)]*\)\s*\{|'
            r'(?:export\s+)?class\s+\w+\s*\{|'
            r'(?:const|let|var)\s+\w+\s*=\s*(?:async\s*)?\([^)]*\)\s*=>\s*\{)',
            re.MULTILINE
        )
        
        matches = list(pattern.finditer(source))
        if not matches:
            return self.char_chunker.chunk_document(document)
            
        chunks = []
        for i in range(len(matches)):
            start = matches[i].start()
            end = matches[i+1].start() if i+1 < len(list(matches)) else len(source)
            content = source[start:end].strip()
            
            if content:
                chunks.append(Document(
                    page_content=content,
                    metadata={
                        **document.metadata,
                        "type": "code_block",
                        "index": i
                    }
                ))
        return chunks


    def chunk_document_list(self, documents: List[Document]) -> List[Document]:
        """Split multiple documents into chunks using AST strategy."""
        all_chunks = []
        for doc in documents:
            all_chunks.extend(self.chunk_document(doc))
        return all_chunks


def print_chunking_stats(stats: Dict[str, Any]):
    """Pretty print chunking statistics."""
    print(f"  Documents: {stats.get('original_documents', 0)}")
    print(f"  Chunks:    {stats.get('total_chunks', 0)}")
    print(f"  Avg size:  {stats.get('avg_chunk_size', 0)} chars")
    print(f"  Range:     {stats.get('min_chunk_size', 0)}-{stats.get('max_chunk_size', 0)} chars")
