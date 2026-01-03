import os
import glob
from pathlib import Path

class FileSystemTool:
    def __init__(self, allowed_paths=None):
        # In a real app, strict sandboxing is crucial.
        # For this prototype, we'll allow reading provided user paths.
        self.allowed_paths = allowed_paths if allowed_paths else ["/"]
        
    def list_directory(self, path: str):
        """List files in a directory"""
        try:
            p = Path(path).expanduser()
            if not p.exists():
                return {"error": f"Path not found: {path}"}
            if not p.is_dir():
                return {"error": f"Not a directory: {path}"}
                
            files = []
            for item in p.iterdir():
                files.append({
                    "name": item.name,
                    "type": "directory" if item.is_dir() else "file",
                    "path": str(item)
                })
            return {"files": files}
        except Exception as e:
            return {"error": str(e)}

    def read_file(self, path: str):
        """Read content of a file"""
        try:
            p = Path(path).expanduser()
            if not p.exists():
                return {"error": f"File not found: {path}"}
            if not p.is_file():
                return {"error": f"Not a file: {path}"}
            
            # Check size first
            if p.stat().st_size > 10 * 1024 * 1024: # 10MB limit
                return {"error": "File too large (>10MB)"}
                
            # Basic text reading
            try:
                content = p.read_text(encoding='utf-8')
                # Truncate if too long for context window
                if len(content) > 10000:
                    return {
                        "content": content[:10000] + "\n...[truncated]", 
                        "path": str(p),
                        "truncated": True
                    }
                return {"content": content, "path": str(p)}
            except UnicodeDecodeError:
                return {"error": "Binary file not supported (cannot decode as UTF-8)"}
                
        except Exception as e:
            return {"error": str(e)}
            
    def find_files(self, pattern: str, root_dir: str):
        """Find files matching a pattern using mdfind (Spotlight) for speed"""
        try:
            root = Path(root_dir).expanduser().resolve()
            if not root.exists():
                return {"error": f"Path not found: {root_dir}"}
                
            # Clean pattern for mdfind (remove * as it implies wildcard by default typically, 
            # or keep them if using -name). 
            # mdfind -name "pattern" works well.
            # However, mdfind searches the whole system. We must filter by root_dir.
            
            # Clean pattern
            clean_pattern = pattern.replace("*", "")
            
            # Using mdfind -name is robust
            import subprocess
            cmd = ["mdfind", "-name", clean_pattern]
            
            # Run command
            output = subprocess.check_output(cmd, text=True)
            all_paths = output.splitlines()
            
            # Filter results
            results = []
            
            # Common noise directories to ignore
            IGNORE_DIRS = {
                "/Library/", "/DerivedData/", "/node_modules/", "/.git/", 
                "/.vscode/", "/__pycache__/", "/.DS_Store", "/venv/"
            }
            
            for path_str in all_paths:
                # 1. Must match root_dir
                if not path_str.startswith(str(root)):
                    continue
                    
                # 2. Must not be in ignore list
                if any(ignore in path_str for ignore in IGNORE_DIRS):
                    continue
                    
                p = Path(path_str)
                results.append(p)
                if len(results) >= 20: break
            
            # Format results
            files = []
            for p in results:
                type_label = "[DIR]" if p.is_dir() else "[FILE]"
                files.append(f"{type_label} {str(p)}")
                
            return {"matches": files, "count": len(results), "truncated": len(results) >= 20}
        except Exception as e:
            return {"error": str(e)}
