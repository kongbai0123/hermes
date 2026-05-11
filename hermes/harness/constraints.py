import re
from typing import List, Tuple

class ConstraintValidator:
    def __init__(self):
        # 禁止執行的危險指令模式
        self.blacklist_patterns = [
            r"rm\s+-rf\s+/",         # 刪除根目錄
            r"mkfs",                 # 格式化磁碟
            r"dd\s+if=.*of=/dev/.*", # 破壞性寫入設備
            r"shutdown",             # 關機
            r"reboot",               # 重啟
            r":\(\)\{ :\|:& \};:"    # 叉子炸彈 (Fork bomb)
        ]
        
        # 允許的操作範圍 (例如僅限特定目錄)
        self.allowed_paths = ["e:/program/hermes"]

    def validate_command(self, command: str) -> Tuple[bool, str]:
        for pattern in self.blacklist_patterns:
            if re.search(pattern, command, re.IGNORECASE):
                return False, f"Blocked dangerous command: {command}"
        return True, "Safe"

    def validate_file_access(self, path: str) -> Tuple[bool, str]:
        # 簡單的路徑檢查
        abs_path = path.lower().replace("\\", "/")
        for allowed in self.allowed_paths:
            if abs_path.startswith(allowed.lower()):
                return True, "Access granted"
        return False, f"Access denied: {path} is outside allowed workspace."

class PermissionGate:
    def __init__(self, mode: str = "HITL"):
        # HITL: Human-in-the-loop
        # AUTO: Auto-approve safe operations
        self.mode = mode

    def request_permission(self, action: str) -> bool:
        if self.mode == "AUTO":
            return True
        print(f"\n[!] PERMISSION REQUEST: {action}")
        # 在實際 UI 中，這裡會彈出對話框
        return True # 目前預設核准
