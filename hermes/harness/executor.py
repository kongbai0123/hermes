import os
from pathlib import Path
from typing import Optional
from hermes.harness.constraints import ConstraintValidator
from hermes.core.types import ToolResult

class SafeExecutor:
    """
    安全執行器: 負責在 Harness 約束下執行唯讀工具。
    """
    def __init__(self, constraints: ConstraintValidator):
        self.constraints = constraints
        self.max_read_chars = 12000
        self.max_list_entries = 200

    def read_file(self, path: str, max_chars: Optional[int] = None) -> ToolResult:
        """讀取檔案內容，支援自動截斷"""
        limit = max_chars or self.max_read_chars
        is_safe, target_path_str = self.constraints.validate_path(path)
        
        if not is_safe:
            return ToolResult(ok=False, tool="read_file", summary="Access Denied", error=target_path_str)
        
        try:
            target_path = Path(target_path_str)
            if not target_path.is_file():
                return ToolResult(ok=False, tool="read_file", summary="Not a file", error=f"Target [{path}] is not a file.")
            
            # 讀取並檢查截斷
            with open(target_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read(limit + 1)
            
            truncated = len(content) > limit
            final_content = content[:limit]
            
            return ToolResult(
                ok=True,
                tool="read_file",
                summary=f"Successfully read {len(final_content)} characters.",
                content=final_content,
                metadata={"truncated": truncated, "path": str(target_path)}
            )
        except Exception as e:
            return ToolResult(ok=False, tool="read_file", summary="Read Error", error=str(e))

    def list_files(self, path: str = ".", max_entries: Optional[int] = None) -> ToolResult:
        """列出目錄清單"""
        limit = max_entries or self.max_list_entries
        is_safe, target_path_str = self.constraints.validate_path(path)
        
        if not is_safe:
            return ToolResult(ok=False, tool="list_files", summary="Access Denied", error=target_path_str)
        
        try:
            target_path = Path(target_path_str)
            if not target_path.is_dir():
                return ToolResult(ok=False, tool="list_files", summary="Not a directory", error=f"Target [{path}] is not a directory.")
            
            items = []
            for item in target_path.iterdir():
                if len(items) >= limit: break
                prefix = "[D] " if item.is_dir() else "[F] "
                items.append(f"{prefix}{item.name}")
            
            return ToolResult(
                ok=True,
                tool="list_files",
                summary=f"Found {len(items)} items in {path}",
                content="\n".join(sorted(items))
            )
        except Exception as e:
            return ToolResult(ok=False, tool="list_files", summary="List Error", error=str(e))

    def execute_shell(self, command: str) -> ToolResult:
        return ToolResult(ok=False, tool="execute_shell", summary="Disabled", error="Shell execution is DISABLED in READ_ONLY mode.")

    def write_file(self, path: str, content: str) -> ToolResult:
        return ToolResult(ok=False, tool="write_file", summary="Disabled", error="File writing is DISABLED in READ_ONLY mode.")
