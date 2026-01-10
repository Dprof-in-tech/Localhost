import os
from pathlib import Path

class SecurityError(Exception):
    pass

class SecuritySandbox:
    def __init__(self):
        self.project_root = None
        # Always block these system paths
        self.blocked_prefixes = [
            "/etc", "/var", "/private", "/sbin", "/usr/sbin", 
            "/boot", "/root", "/.ssh"
        ]

    def set_project_root(self, path: str):
        """Set the active project root for WRITE operations. Pass None to clear."""
        if path is None:
            self.project_root = None
            return "Context Cleared"
            
        resolved = Path(path).expanduser().resolve()
        if not resolved.exists():
            raise FileNotFoundError(f"Project path does not exist: {resolved}")
        self.project_root = resolved
        return str(self.project_root)

    def validate_path(self, target_path: str, operation: str = "READ") -> Path:
        """
        Validate if a path is safe to access.
        READ: Allowed globally (except blocked system paths).
        WRITE: Must be within self.project_root.
        """
        target = Path(target_path).expanduser().resolve()
        target_str = str(target)
        
        # 1. Global Blocklist (for both READ and WRITE)
        for prefix in self.blocked_prefixes:
            if target_str.startswith(prefix):
                raise SecurityError(f"Access DENIED: Restricted system path {prefix}")

        # 2. Operation specific checks
        if operation == "WRITE":
            if not self.project_root:
                raise SecurityError("Write Denied: No active project set. Use /project <path> first.")
            
            # Check if target is inside project_root
            # is_relative_to is efficient and safe
            try:
                target.relative_to(self.project_root)
            except ValueError:
                # Fallback for Case-Insensitive systems (macOS/Windows)
                # If /Users/Prof vs /users/prof mismatch occurs
                if str(target).lower().startswith(str(self.project_root).lower()):
                    return target
                
                print(f"SECURITY ALERT: Write Denied. Target: {target} | Root: {self.project_root}")
                raise SecurityError(f"Write Denied: Path is outside active project ({self.project_root})")

        return target
