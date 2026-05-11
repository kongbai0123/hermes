import os
from pathlib import Path
from typing import Tuple, Optional

class ConstraintValidator:
    """
    Harness 安全約束器: 確保 Agent 行為不超出預設邊界。
    """
    def __init__(self, workspace_root: Optional[str] = None):
        # 優先順序: 手動指定 > 環境變數 > 當前目錄
        env_root = os.getenv("HERMES_WORKSPACE")
        self.workspace_root = Path(env_root or workspace_root or ".").resolve()
        
        # 允許的文字型副檔名
        self.allowed_extensions = {
            '.py', '.md', '.txt', '.json', '.yaml', '.yml', 
            '.html', '.css', '.js', '.ts', '.toml', '.ini', '.bat', '.sh'
        }
        
        # 絕對禁止訪問的敏感項目
        self.forbidden_segments = {
            '.env', '.git', '.venv', 'node_modules', 
            '__pycache__', 'secrets', '.vscode', '.idea'
        }

    def validate_path(self, path: str) -> Tuple[bool, str]:
        """
        驗證路徑安全性：
        1. 必須在 workspace 內 (防範 ../ 逃逸)
        2. 禁止敏感名稱
        3. 副檔名檢查 (防範二進位)
        4. 檔案大小檢查 (限 512KB)
        """
        try:
            target_path = Path(path)
            # resolve() 會解析所有 .. 並返回規範路徑
            if not target_path.is_absolute():
                target_path = (self.workspace_root / target_path).resolve()
            else:
                target_path = target_path.resolve()

            # 1. 邊界檢查
            if not str(target_path).startswith(str(self.workspace_root)):
                return False, f"Access Denied: Path [{path}] is outside workspace boundary."

            # 2. 敏感檔案檢查
            parts = set(target_path.parts)
            if parts.intersection(self.forbidden_segments) or target_path.name in self.forbidden_segments:
                return False, f"Access Denied: Path contains forbidden items."

            # 3. 檔案屬性檢查
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
        """v1 唯讀模式下嚴禁執行任何命令"""
        return False, "Shell execution is strictly DISABLED in READ_ONLY mode."
