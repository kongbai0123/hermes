import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from hermes.harness.constraints import ConstraintValidator
from hermes.core.types import ToolResult

class SafeExecutor:
    """
    安全執行器: 負責在 Harness 約束下執行工具。
    V1 版本僅開放唯讀操作。
    """
    def __init__(self, constraints: ConstraintValidator):
        self.constraints = constraints
        self.max_read_chars = 12000
        self.max_file_size = 512 * 1024  # 512 KB

    def list_files(self, directory: str = ".") -> ToolResult:
        """列出指定目錄下的檔案與子目錄"""
        is_safe, target_path_str = self.constraints.validate_file_access(directory)
        if not is_safe:
            return ToolResult(ok=False, tool="list_files", summary="Access Denied", error=target_path_str)
        
        try:
            target_path = Path(target_path_str)
            if not target_path.is_dir():
                return ToolResult(ok=False, tool="list_files", summary="Not a directory", error=f"{directory} is not a directory")
            
            items = []
            for item in target_path.iterdir():
                prefix = "[D] " if item.is_dir() else "[F] "
                items.append(f"{prefix}{item.name}")
            
            content = "\n".join(sorted(items))
            return ToolResult(
                ok=True, 
                tool="list_files", 
                summary=f"Found {len(items)} items in {directory}",
                content=content
            )
        except Exception as e:
            return ToolResult(ok=False, tool="list_files", summary="Execution Error", error=str(e))

    def read_file(self, file_path: str) -> ToolResult:
        """讀取指定檔案內容，支援自動截斷"""
        is_safe, target_path_str = self.constraints.validate_file_access(file_path)
        if not is_safe:
            return ToolResult(ok=False, tool="read_file", summary="Access Denied", error=target_path_str)
        
        try:
            target_path = Path(target_path_str)
            if not target_path.is_file():
                return ToolResult(ok=False, tool="read_file", summary="Not a file", error=f"{file_path} is not a file")
            
            # 檔案大小檢查
            file_size = target_path.stat().st_size
            if file_size > self.max_file_size:
                return ToolResult(ok=False, tool="read_file", summary="File too large", error=f"File exceeds {self.max_file_size/1024}KB limit")
            
            with open(target_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read(self.max_read_chars + 1)
            
            truncated = len(content) > self.max_read_chars
            final_content = content[:self.max_read_chars]
            
            return ToolResult(
                ok=True,
                tool="read_file",
                summary=f"Read success ({len(final_content)} chars)",
                content=final_content,
                metadata={
                    "truncated": truncated,
                    "original_size": file_size,
                    "path": str(target_path)
                }
            )
        except Exception as e:
            return ToolResult(ok=False, tool="read_file", summary="Execution Error", error=str(e))

    def execute_shell(self, command: str) -> ToolResult:
        return ToolResult(ok=False, tool="shell", summary="Disabled", error="Shell execution is disabled in v1.")

    def write_file(self, path: str, content: str) -> ToolResult:
        return ToolResult(ok=False, tool="write_file", summary="Disabled", error="File writing is disabled in v1.")
