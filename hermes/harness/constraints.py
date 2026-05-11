import os
from pathlib import Path
from typing import Tuple, Optional

class ConstraintValidator:
    """
    Harness 安全約束器: 確保 Agent 行為不超出預設邊界。
    """
    def __init__(self, workspace_root: Optional[str] = None):
        # 支援環境變數或手動指定，預設為當前目錄
        env_root = os.getenv("HERMES_WORKSPACE")
        self.workspace_root = Path(env_root or workspace_root or ".").resolve()
        
        # 文字型檔案白名單
        self.allowed_extensions = {
            '.py', '.md', '.txt', '.json', '.yaml', '.yml', 
            '.html', '.css', '.js', '.ts', '.toml', '.ini', '.bat', '.sh'
        }
        
        # 敏感路徑屏蔽
        self.forbidden_segments = {
            '.env', '.git', '.venv', 'node_modules', 
            '__pycache__', 'secrets', '.vscode', '.idea'
        }

    def validate_path(self, path: str) -> Tuple[bool, str]:
        """
        驗證路徑安全性：
        1. 必須在 workspace 內。
        2. 禁止訪問敏感項目。
        3. 副檔名必須在白名單內。
        4. 檔案大小不得超過 512KB。
        """
        try:
            target_path = Path(path)
            # resolve() 會處理 ../ 並解析 symlink
            if not target_path.is_absolute():
                target_path = (self.workspace_root / target_path).resolve()
            else:
                target_path = target_path.resolve()

            # 1. 邊界檢查
            if not str(target_path).startswith(str(self.workspace_root)):
                return False, f"Access Denied: Path [{path}] is outside workspace boundary."

            # 2. 敏感項目檢查 (包含檔案名與路徑片段)
            parts = set(target_path.parts)
            if parts.intersection(self.forbidden_segments) or target_path.name in self.forbidden_segments:
                return False, f"Access Denied: Forbidden item detected in path."

            # 3. 檔案類型與大小檢查
            if target_path.is_file():
                ext = target_path.suffix.lower()
                if ext not in self.allowed_extensions and target_path.name not in {'.gitignore', 'LICENSE'}:
                    return False, f"Access Denied: Unsupported file type ({ext})."
                
                if target_path.stat().st_size > 512 * 1024:
                    return False, "Access Denied: File size exceeds 512KB limit."

            return True, str(target_path)
        except Exception as e:
            return False, f"Validation Error: {str(e)}"

    def validate_command(self, command: str) -> Tuple[bool, str]:
        """v1 階段嚴禁 Shell 執行"""
        return False, "Shell execution is strictly DISABLED in READ_ONLY mode."
