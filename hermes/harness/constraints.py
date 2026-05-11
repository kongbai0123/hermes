import os
from pathlib import Path
from typing import Tuple, List, Optional

class ConstraintValidator:
    """
    Harness 安全約束器: 確保 Agent 行為不超出預設邊界。
    """
    def __init__(self, workspace_root: Optional[str] = None):
        # 優先順序: 手動指定 > 環境變數 > 預設當前路徑
        env_root = os.getenv("HERMES_WORKSPACE")
        self.workspace_root = Path(env_root or workspace_root or ".").resolve()
        
        # 允許讀取的檔案副檔名 (白名單)
        self.allowed_extensions = {
            '.py', '.md', '.txt', '.json', '.yaml', '.yml', 
            '.html', '.css', '.js', '.ts', '.toml', '.ini', '.bat', '.sh'
        }
        
        # 絕對禁止訪問的敏感目錄或檔案名稱
        self.forbidden_segments = {
            '.env', '.git', '.venv', 'node_modules', 
            '__pycache__', 'secrets', '.vscode', '.idea'
        }
        
        # 禁止的二進位副檔名
        self.binary_extensions = {'.exe', '.dll', '.bin', '.gguf', '.pt', '.onnx', '.so', '.dylib'}

    def validate_path(self, path: str) -> Tuple[bool, str]:
        """
        驗證路徑安全性：
        1. 必須在庫中 (Workspace Boundary)
        2. 禁止敏感名稱 (.env, .git ...)
        3. 必須是允許的副檔名 (二進位封鎖)
        """
        try:
            target_path = Path(path)
            # 轉換為絕對路徑並解析 symlink
            if not target_path.is_absolute():
                target_path = (self.workspace_root / target_path).resolve()
            else:
                target_path = target_path.resolve()

            # 1. 邊界檢查: 是否在 workspace 之下
            if not str(target_path).startswith(str(self.workspace_root)):
                return False, f"Access Denied: Path [{path}] is outside workspace boundary."

            # 2. 敏感檔案/路徑檢查 (檢查所有路徑片段)
            parts = set(target_path.parts)
            if parts.intersection(self.forbidden_segments):
                return False, f"Access Denied: Path contains forbidden items (.env, .git, etc.)"

            # 3. 副檔名與二進位檢查
            if target_path.is_file():
                ext = target_path.suffix.lower()
                if ext in self.binary_extensions:
                    return False, f"Access Denied: Binary files ({ext}) are strictly blocked."
                if ext not in self.allowed_extensions and target_path.name not in {'.gitignore', 'LICENSE'}:
                    return False, f"Access Denied: Unsupported file type ({ext})."

            return True, str(target_path)
        except Exception as e:
            return False, f"Validation Error: {str(e)}"

    def validate_command(self, command: str) -> Tuple[bool, str]:
        """v1 階段暫不開放任何 Shell 執行"""
        return False, "Shell execution is strictly DISABLED in Read-Only mode."
