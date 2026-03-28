"""
Code Parsing and Metadata Extraction.

Parses code files using AST to extract functions, classes, imports, 
and other structural metadata for enriching RAG documents.
"""

import ast
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict


@dataclass
class CodeMetadata:
    """Metadata extracted from code files."""
    functions: List[Dict[str, Any]]
    classes: List[Dict[str, Any]]
    imports: List[str]
    calls: List[str]  # NEW: List of function/method names called in this file
    docstring: Optional[str]
    language: str
    file_path: str
    file_size: int
    line_count: int
    complexity: int = 0


@dataclass
class CodeDocument:
    """Document representing a code file with metadata."""
    content: str
    metadata: CodeMetadata

    def to_dict(self) -> Dict[str, Any]:
        return {
            "content": self.content,
            "metadata": asdict(self.metadata)
        }


class PythonParser:
    """Parser for Python code using AST."""

    @staticmethod
    def parse(file_path: Path, content: str) -> CodeMetadata:
        """Parse Python file and extract metadata."""
        try:
            tree = ast.parse(content)
        except SyntaxError as e:
            return CodeMetadata(
                functions=[], classes=[], imports=[], calls=[],
                docstring=f"Syntax Error: {str(e)}",
                language="python",
                file_path=str(file_path),
                file_size=len(content),
                line_count=content.count('\n') + 1
            )

        functions = []
        classes = []
        imports = []
        calls = []
        complexity = 0

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                func_data = {
                    "name": node.name,
                    "args": [arg.arg for arg in node.args.args],
                    "returns": ast.unparse(node.returns) if node.returns else None,
                    "lineno": node.lineno,
                    "end_lineno": node.end_lineno,
                    "docstring": ast.get_docstring(node),
                    "decorators": [ast.unparse(d) for d in node.decorator_list],
                    "is_async": isinstance(node, ast.AsyncFunctionDef),
                    "is_method": False
                }
                functions.append(func_data)
                complexity += 1

            elif isinstance(node, ast.ClassDef):
                methods = []
                for item in node.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        methods.append({
                            "name": item.name,
                            "lineno": item.lineno,
                            "docstring": ast.get_docstring(item)
                        })
                classes.append({
                    "name": node.name,
                    "methods": methods,
                    "bases": [ast.unparse(base) for base in node.bases],
                    "lineno": node.lineno,
                    "end_lineno": node.end_lineno,
                    "docstring": ast.get_docstring(node),
                    "decorators": [ast.unparse(d) for d in node.decorator_list]
                })
                complexity += len(methods) + 1

            elif isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)

            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for alias in node.names:
                    full_import = f"{module}.{alias.name}" if module else alias.name
                    imports.append(full_import)

            elif isinstance(node, ast.Call):
                # Extract function calls (e.g., func(), obj.method())
                if isinstance(node.func, ast.Name):
                    calls.append(node.func.id)
                elif isinstance(node.func, ast.Attribute):
                    calls.append(node.func.attr)

        return CodeMetadata(
            functions=functions,
            classes=classes,
            imports=list(set(imports)),
            calls=list(set(calls)),
            docstring=ast.get_docstring(tree),
            language="python",
            file_path=str(file_path),
            file_size=len(content),
            line_count=content.count('\n') + 1,
            complexity=complexity
        )


class JavaScriptParser:
    """Basic parser for JavaScript/TypeScript files (no AST, pattern-based)."""

    @staticmethod
    def parse(file_path: Path, content: str) -> CodeMetadata:
        """Parse JS/TS file with basic pattern matching."""
        import re

        functions = []
        classes = []
        imports = []
        calls = []

        lines = content.split('\n')

        for i, line in enumerate(lines, 1):
            stripped = line.strip()

            # Imports
            if stripped.startswith('import ') or stripped.startswith('const ') and 'require(' in stripped:
                imports.append(stripped)

            # Functions
            func_patterns = [
                r'(?:export\s+)?(?:async\s+)?function\s+(\w+)',
                r'(?:export\s+)?const\s+(\w+)\s*=\s*(?:async\s*)?\(',
                r'(?:export\s+)?const\s+(\w+)\s*=\s*(?:async\s*)?\w*\s*=>\s*',
            ]
            for pattern in func_patterns:
                match = re.match(pattern, stripped)
                if match:
                    functions.append({
                        "name": match.group(1),
                        "lineno": i,
                        "is_async": "async" in stripped,
                    })
                    break

            # Classes
            class_match = re.match(r'(?:export\s+)?class\s+(\w+)', stripped)
            if class_match:
                classes.append({
                    "name": class_match.group(1),
                    "lineno": i,
                    "methods": [],
                })

            # CALLS (Basic regex)
            # Find all words followed by ( that are not keywords
            found_calls = re.findall(r'(\w+)\s*\(', stripped)
            keywords = {'if', 'for', 'while', 'switch', 'catch', 'function', 'class', 'await'}
            for c in found_calls:
                if c not in keywords:
                    calls.append(c)

        ext = file_path.suffix.lstrip('.') if file_path.suffix else "" # Remove dot
        lang_map = {'js': 'javascript', 'jsx': 'javascript', 'ts': 'typescript', 'tsx': 'typescript'}
        language = lang_map.get(ext, ext)

        return CodeMetadata(
            functions=functions,
            classes=classes,
            imports=imports,
            calls=calls,
            docstring=None,
            language=language,
            file_path=str(file_path),
            file_size=len(content),
            line_count=len(lines),
            complexity=len(functions) + len(classes)
        )
