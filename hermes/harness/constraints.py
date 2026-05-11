import os
from pathlib import Path
from typing import Tuple, List, Optional

class ConstraintValidator:
    """
    Harness 安全約束器: 確保 Agent 行為不超出預設邊界。
    """
    def __init__(self, workspace_root: Optional[str] = None):
        # 預設工作區根目錄 (優先使用環境變數)
        env_root = os.getenv("HERMES_WORKSPACE")
        self.workspace_root = Path(env_root or workspace_root or "e:/program/hermes").resolve()
        
        # 允許讀取的檔案副檔名 (白名單)
        self.allowed_extensions = {
            '.py', '.md', '.txt', '.json', '.yaml', '.yml', 
            '.html', '.css', '.js', '.ts', '.toml', '.ini'
        }
        
        # 絕對禁止訪問的敏感路徑或檔案
        self.forbidden_names = {'.env', '.git', 'node_modules', 'secrets', '__pycache__'}

    def validate_file_access(self, path: str) -> Tuple[bool, str]:
        """
        驗證路徑安全性：
        1. 必須在庫中 (Workspace Boundary)
        2. 禁止敏感名稱 (.env)
        3. 必須是允許的副檔名 (Binary Blocking)
        """
        try:
            target_path = Path(path)
            # 如果是相對路徑，則相對於工作區
            if not target_path.is_absolute():
                target_path = (self.workspace_root / target_path).resolve()
            else:
                target_path = target_path.resolve()

            # 1. 邊界檢查 (Symlink Escape Prevention)
            if not str(target_path).startswith(str(self.workspace_root)):
                return False, f"Access Denied: Path is outside workspace boundary."

            # 2. 敏感檔案檢查
            if any(name in target_path.parts for name in self.forbidden_names) or target_path.name in self.forbidden_names:
                return False, f"Access Denied: Requested path contains forbidden system/sensitive items."

            # 3. 檔案類型檢查 (僅針對檔案讀取)
            if target_path.is_file():
                if target_path.suffix.lower() not in self.allowed_extensions:
                    return False, f"Access Denied: File type {target_path.suffix} is blocked (Binary/Unsupported)."

            return True, str(target_path)
        except Exception as e:
            return False, f"Validation Error: {str(e)}"

    def validate_command(self, command: str) -> Tuple[bool, str]:
        """v1 階段暫不開放 Shell 執行"""
        return False, "Shell execution is currently disabled in Read-Only mode."
