# hermes/harness/constraints.py
import os
from pathlib import Path
from typing import Tuple, Optional

class ConstraintValidator:
    def __init__(self, workspace_root: Optional[str] = None):
        env_root = os.getenv("HERMES_WORKSPACE")
        self.workspace_root = Path(env_root or workspace_root or ".").resolve()
        self.allowed_extensions = {
            '.py', '.md', '.txt', '.json', '.yaml', '.yml', 
            '.html', '.css', '.js', '.ts', '.toml', '.ini', '.bat', '.sh'
        }
        self.forbidden_segments = {
            '.env', '.git', '.venv', 'node_modules', 
            '__pycache__', 'secrets', '.vscode', '.idea'
        }

    def validate_path(self, path: str) -> Tuple[bool, str]:
        try:
            target_path = Path(path)
            if not target_path.is_absolute():
                target_path = (self.workspace_root / target_path).resolve()
            else:
                target_path = target_path.resolve()

            if not str(target_path).startswith(str(self.workspace_root)):
                return False, f"Access Denied: Outside workspace boundary."

            parts = set(target_path.parts)
            if parts.intersection(self.forbidden_segments) or target_path.name in self.forbidden_segments:
                return False, f"Access Denied: Forbidden item detected."

            if target_path.is_file():
                if target_path.suffix.lower() not in self.allowed_extensions and target_path.name not in {'.gitignore', 'LICENSE'}:
                    return False, f"Access Denied: Unsupported file type ({target_path.suffix})."
                if target_path.stat().st_size > 512 * 1024:
                    return False, "Access Denied: File size exceeds 512KB limit."

            return True, str(target_path)
        except Exception as e:
            return False, str(e)

# hermes/harness/executor.py (APPENDED BELOW FOR SPEED)
# Note: In actual execution, I will split these.
