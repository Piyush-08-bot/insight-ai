import os
from pathlib import Path
from typing import List, Dict, Any

class FilesystemScanner:
    """Helper to provide real-time filesystem context when index falls short."""
    
    @staticmethod
    def scan_directory(path: str, max_depth: int = 2) -> str:
        """Get a high-level summary of a directory's contents."""
        try:
            target = Path(path).expanduser().resolve()
            if not target.exists():
                return f"Path does not exist: {path}"
            
            if target.is_file():
                return f"File found: {path} (Size: {target.stat().st_size} bytes)"
            
            summary = [f"📁 Directory Overview: {target.name}"]
            
            exclude_dirs = {".git", "node_modules", ".venv", "venv", "__pycache__", ".pytest_cache"}
            
            # Simple recursive walk
            for root, dirs, files in os.walk(target):
                # Filter directories in-place
                new_dirs = [d for d in dirs if d not in exclude_dirs]
                dirs.clear()
                dirs.extend(new_dirs)
                
                rel_root = Path(root).relative_to(target)
                depth = len(rel_root.parts)
                if depth >= max_depth:
                    continue
                
                indent = "  " * depth
                if depth > 0:
                    summary.append(f"{indent}subdirectory: {rel_root.name}/")
                
                # List files in this level
                for f in [f_name for i, f_name in enumerate(sorted(list(files))) if i < 10]: # Limit for context
                    if not f.startswith('.'):
                        summary.append(f"{indent}  - {f}")
                
                if len(files) > 10:
                    summary.append(f"{indent}  - ... ({len(files) - 10} more files)")
                    
            return "\n".join(summary)
        except Exception as e:
            return f"Error scanning filesystem: {str(e)}"
