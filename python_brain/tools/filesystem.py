import difflib
from pathlib import Path
from security.sandbox import SecuritySandbox
from tools.formatter import ContentFormatter

class FileSystemTool:
    def __init__(self, allowed_paths=None):
        self.sandbox = SecuritySandbox()
        self.pending_edits = [] # List of {path, content}

    def set_project_root(self, path: str):
        return self.sandbox.set_project_root(path)

    # ... (keeping list_directory, read_file, find_files as is) ...

    def write_file(self, path: str, content: str):
        """Propose a file write (Draft Mode). Requires /approve to execute."""
        try:
            # 1. Validate Scope (WRITE check)
            p = self.sandbox.validate_path(path, "WRITE")
            
            # 2. Auto-Format Content (User Request)
            # This ensures JSON is pretty and MD has proper spacing
            content = ContentFormatter.format(content, str(p))
            
            # 3. Generate Diff
            old_content = ""
            if p.exists():
                try:
                    old_content = p.read_text(encoding='utf-8')
                    
                    # SAFETY GUARD: Anti-Destruction Check
                    # If overwriting a file with content < 70% of original size, verify intent.
                    if len(content) < len(old_content) * 0.70:
                         return {
                             "error": f"SAFETY ALERT: You are about to delete {len(old_content) - len(content)} chars (~{int((1 - len(content)/len(old_content))*100)}% of file). \nSTOP. Do NOT overwrite the file. \nUse `replace_in_file` to modify specific sections safely."
                         }

                except:
                    return {"error": "Cannot read existing file (binary?)"}
            
            diff = difflib.unified_diff(
                old_content.splitlines(keepends=True),
                content.splitlines(keepends=True),
                fromfile=f"a/{p.name}",
                tofile=f"b/{p.name}"
            )
            diff_text = "".join(diff)
            
            # 3. Store Pending Edit
            self.pending_edits.append({
                "path": p,
                "content": content
            })
            
            return f"📝 DRAFT CREATED for {p.name}\nTYPE: /approve TO APPLY.\n\nDIFF:\n{diff_text}\n\n[SYSTEM WARNING: This is a DRAFT. Do NOT tell the user it is applied. Tell them it is PENDING approval.]"
            
        except Exception as e:
            return {"error": str(e)}

    def replace_file_content(self, path: str, target_block: str, replacement_block: str):
        """Propose a partial edit (search & replace). Requires /approve."""
        try:
            # 1. Validate Scope
            p = self.sandbox.validate_path(path, "WRITE")
            
            if not p.exists():
                return {"error": f"File not found: {path}"}
                
            original_content = p.read_text(encoding='utf-8')
            
            # 2. Strict Search
            if target_block not in original_content:
                # Try relaxed search (strip whitespace)
                if target_block.strip() in original_content:
                    return {"error": "Target found but whitespace differs. Please allow sloppy search or be exact."}
                return {"error": "Target block not found in file. Please Use 'read_file' to verify exact content."}
            
            # 3. Apply Replacement
            new_content = original_content.replace(target_block, replacement_block, 1) # Only replace first occurrence for safety
            
            # 4. Generate Diff
            diff = difflib.unified_diff(
                original_content.splitlines(keepends=True),
                new_content.splitlines(keepends=True),
                fromfile=f"a/{p.name}",
                tofile=f"b/{p.name}"
            )
            diff_text = "".join(diff)
            
            # 5. Store Pending Edit
            self.pending_edits.append({
                "path": p,
                "content": new_content
            })
            
            return f"DRAFT (Partial) CREATED for {p.name}\nTYPE: /approve TO APPLY.\n\nDIFF:\n{diff_text}"
            
        except Exception as e:
            return {"error": str(e)}

    def approve_pending_edits(self):
        """Apply all pending edits"""
        if not self.pending_edits:
            return "No pending edits."
            
        results = []
        for edit in self.pending_edits:
            try:
                # Re-validate just in case
                p = self.sandbox.validate_path(str(edit["path"]), "WRITE")
                p.write_text(edit["content"], encoding='utf-8')
                results.append(f"✅ Applied: {p.name}")
            except Exception as e:
                results.append(f"❌ Failed: {p.name} ({e})")
                
        self.pending_edits = []
        return "\n".join(results)
    
    # ... (rest of methods) ...
        
    def list_directory(self, path: str):
        """List files in a directory"""
        try:
            # Security Check
            p = self.sandbox.validate_path(path, "READ")
            
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
            # Security Check
            p = self.sandbox.validate_path(path, "READ")
            
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

    def read_multiple_files(self, *paths):
        """Read content of multiple files. Supports list arg or multiple string args."""
        results = []
        
        # Normalize arguments
        # Case 1: Passed as single list -> (['a', 'b'],)
        if len(paths) == 1 and isinstance(paths[0], list):
            file_list = paths[0]
        # Case 2: Passed as multiple args -> ('a', 'b')
        else:
            file_list = list(paths)

        for path in file_list:
            try:
                # Reuse read_file logic (security checks + size limits + truncation)
                # Note: read_file returns a dictionary or dict-like error
                result = self.read_file(str(path)) # Ensure string
                
                if "error" in result:
                     results.append(f"## File: {path}\n[ERROR] {result['error']}")
                elif "content" in result:
                     content = result["content"]
                     if result.get("truncated"):
                         content += "\n[TRUNCATED]"
                     results.append(f"## File: {path}\n{content}")
                else:
                     results.append(f"## File: {path}\n[UNKNOWN RESULT]")
                     
            except Exception as e:
                results.append(f"## File: {path}\n[SYSTEM ERROR] {e}")
                
        return "\n\n" + ("="*40) + "\n\n".join(results) + "\n" + ("="*40)

            
    def find_files(self, pattern: str, root_dir: str = None):
        """Find files matching a pattern using mdfind (Spotlight) for speed"""
        try:
            # Default to project root if not provided
            if not root_dir:
                if self.sandbox.project_root:
                    root_dir = str(self.sandbox.project_root)
                else:
                     return {"error": "Missing root_dir and no project root set. Use /project <path> first."}

            root = Path(root_dir).expanduser().resolve()
            if not root.exists():
                return {"error": f"Path not found: {root_dir}"}
                
            # Clean pattern for mdfind (remove * as it implies wildcard by default typically, 
            # or keep them if using -name). 
            # mdfind -name "pattern" works well.
            # However, mdfind searches the whole system. We must filter by root_dir.
            
            # Clean pattern
            clean_pattern = pattern.replace("*", "")
            
            # Using mdfind -onlyin is much faster as it filters at the index level
            import subprocess
            cmd = ["mdfind", "-onlyin", str(root), "-name", clean_pattern]
            
            # Run command
            output = subprocess.check_output(cmd, text=True)
            all_paths = output.splitlines()
            
            # Filter results (still need to filter noise, but list is smaller)
            results = []
            
            # Common noise directories to ignore
            IGNORE_DIRS = {
                "/Library/", "/DerivedData/", "/node_modules/", "/.git/", 
                "/.vscode/", "/__pycache__/", "/.DS_Store", "/venv/"
            }
            
            for path_str in all_paths:
                # 1. Must not be in ignore list
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
