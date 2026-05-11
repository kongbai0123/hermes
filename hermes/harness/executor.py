from pathlib import Path
from typing import Optional
from hermes.harness.constraints import ConstraintValidator
from hermes.core.types import ToolResult

class SafeExecutor:
    def __init__(self, constraints: ConstraintValidator):
        self.constraints = constraints
        self.max_read_chars = 12000

    def read_file(self, path: str, max_chars: Optional[int] = None) -> ToolResult:
        limit = max_chars or self.max_read_chars
        is_safe, target_path_str = self.constraints.validate_path(path)
        if not is_safe:
            return ToolResult(ok=False, tool="read_file", summary="Access Denied", error=target_path_str)
        try:
            with open(target_path_str, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read(limit + 1)
            truncated = len(content) > limit
            return ToolResult(ok=True, tool="read_file", summary="Success", content=content[:limit], metadata={"truncated": truncated})
        except Exception as e:
            return ToolResult(ok=False, tool="read_file", summary="Error", error=str(e))

    def list_files(self, path: str = ".", max_entries: int = 200) -> ToolResult:
        is_safe, target_path_str = self.constraints.validate_path(path)
        if not is_safe:
            return ToolResult(ok=False, tool="list_files", summary="Access Denied", error=target_path_str)
        try:
            target_path = Path(target_path_str)
            items = [("[D] " if i.is_dir() else "[F] ") + i.name for i in list(target_path.iterdir())[:max_entries]]
            return ToolResult(ok=True, tool="list_files", summary="Success", content="\n".join(sorted(items)))
        except Exception as e:
            return ToolResult(ok=False, tool="list_files", summary="Error", error=str(e))

    def execute_shell(self, command: str) -> ToolResult:
        return ToolResult(ok=False, tool="execute_shell", summary="Disabled", error="Shell disabled in READ_ONLY mode.")

    def write_file(self, path: str, content: str) -> ToolResult:
        return ToolResult(ok=False, tool="write_file", summary="Disabled", error="Writing disabled in READ_ONLY mode.")
