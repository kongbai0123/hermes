import subprocess
import os
from typing import Tuple, Dict, Any
from hermes.harness.constraints import ConstraintValidator
from hermes.harness.governance import GovernanceManager

class SafeExecutor:
    """
    安全執行引擎: 負責受限環境下的指令執行。
    """
    def __init__(self, constraints: ConstraintValidator, governance: GovernanceManager):
        self.constraints = constraints
        self.governance = governance

    def execute_shell(self, command: str) -> Tuple[bool, str]:
        # 1. 檢查治理層權限
        if not self.governance.is_authorized("shell_execute"):
            return False, "Permission denied: shell_execute is not granted."
        
        # 2. 檢查安全限制 (Harness)
        is_safe, msg = self.constraints.validate_command(command)
        if not is_safe:
            return False, msg

        # 3. 執行指令 (模擬受限環境)
        try:
            # 實際執行時應加入 timeout 與 cwd 限制
            result = subprocess.run(
                command, 
                shell=True, 
                capture_output=True, 
                text=True, 
                timeout=30,
                cwd="e:/program/hermes" # 強制在工作目錄執行
            )
            
            if result.returncode == 0:
                return True, result.stdout
            else:
                return False, result.stderr
        except Exception as e:
            return False, str(e)

    def write_file(self, path: str, content: str) -> Tuple[bool, str]:
        if not self.governance.is_authorized("filesystem_write"):
            return False, "Permission denied: filesystem_write is not granted."
            
        is_safe, msg = self.constraints.validate_file_access(path)
        if not is_safe:
            return False, msg
            
        try:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True, f"Successfully wrote to {path}"
        except Exception as e:
            return False, str(e)
