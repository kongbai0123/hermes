from pathlib import Path
from typing import Optional, Any
from hermes.harness.constraints import ConstraintValidator
from hermes.core.types import ToolResult

class SafeExecutor:
    """
    安全執行器: 負責在 Harness 約束下執行唯讀工具。
    """
    def __init__(self, constraints: ConstraintValidator):
        self.constraints = constraints
        self.max_read_chars = 12000

    def read_file(self, path: str, max_chars: Optional[int] = None) -> ToolResult:
        """讀取檔案，支援截斷"""
        limit = max_chars or self.max_read_chars
        is_safe, target_path_str = self.constraints.validate_path(path)
        
        if not is_safe:
            return ToolResult(ok=False, tool="read_file", summary="Access Denied", error=target_path_str)
        
        try:
            target_path = Path(target_path_str)
            if not target_path.is_file():
                return ToolResult(ok=False, tool="read_file", summary="Not a file", error=f"Target [{path}] is not a file.")
            
            with open(target_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read(limit + 1)
            
            truncated = len(content) > limit
            final_content = content[:limit]
            
            return ToolResult(
                ok=True,
                tool="read_file",
                summary="Read success",
                content=final_content,
                metadata={"truncated": truncated, "path": str(target_path)}
            )
        except Exception as e:
            return ToolResult(ok=False, tool="read_file", summary="Read Error", error=str(e))

    def list_files(self, path: str = ".", max_entries: int = 200) -> ToolResult:
        """列出目錄清單"""
        is_safe, target_path_str = self.constraints.validate_path(path)
        
        if not is_safe:
            return ToolResult(ok=False, tool="list_files", summary="Access Denied", error=target_path_str)
        
        try:
            target_path = Path(target_path_str)
            if not target_path.is_dir():
                return ToolResult(ok=False, tool="list_files", summary="Not a directory", error=f"Target [{path}] is not a directory.")
            
            items = []
            for item in list(target_path.iterdir())[:max_entries]:
                prefix = "[D] " if item.is_dir() else "[F] "
                items.append(f"{prefix}{item.name}")
            
            return ToolResult(
                ok=True,
                tool="list_files",
                summary=f"Found {len(items)} items",
                content="\n".join(sorted(items))
            )
        except Exception as e:
            return ToolResult(ok=False, tool="list_files", summary="List Error", error=str(e))

    def execute_shell(self, command: str) -> ToolResult:
        return ToolResult(ok=False, tool="execute_shell", summary="Disabled", error="Shell is DISABLED in READ_ONLY mode.")

    def write_file(self, path: str, content: str) -> ToolResult:
        return ToolResult(ok=False, tool="write_file", summary="Disabled", error="Writing is DISABLED in READ_ONLY mode.")
