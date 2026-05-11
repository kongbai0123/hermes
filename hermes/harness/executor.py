from pathlib import Path
import subprocess
import unittest
import io
from typing import Optional, Any, List
from hermes.harness.constraints import ConstraintValidator
from hermes.core.types import ToolResult

class SafeExecutor:
    """
    安全執行器 V2: 擴展搜尋與測試能力。
    """
    def __init__(self, constraints: ConstraintValidator):
        self.constraints = constraints
        self.max_read_chars = 12000

    def read_file(self, path: str, max_chars: Optional[int] = None) -> ToolResult:
        limit = max_chars or self.max_read_chars
        is_safe, target_path_str = self.constraints.validate_path(path)
        if not is_safe:
            return ToolResult(ok=False, tool="read_file", summary="Access Denied", error=target_path_str)
        try:
            target_path = Path(target_path_str)
            if not target_path.is_file():
                return ToolResult(ok=False, tool="read_file", summary="Not a file", error=f"Target is not a file.")
            with open(target_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read(limit + 1)
            truncated = len(content) > limit
            return ToolResult(ok=True, tool="read_file", summary="Read success", content=content[:limit], metadata={"truncated": truncated, "path": str(target_path)})
        except Exception as e:
            return ToolResult(ok=False, tool="read_file", summary="Read Error", error=str(e))

    def list_files(self, path: str = ".", max_entries: int = 200) -> ToolResult:
        is_safe, target_path_str = self.constraints.validate_path(path)
        if not is_safe:
            return ToolResult(ok=False, tool="list_files", summary="Access Denied", error=target_path_str)
        try:
            target_path = Path(target_path_str)
            if not target_path.is_dir():
                return ToolResult(ok=False, tool="list_files", summary="Not a directory", error=f"Target is not a directory.")
            items = [f"{'[D] ' if i.is_dir() else '[F] '}{i.name}" for i in list(target_path.iterdir())[:max_entries]]
            return ToolResult(ok=True, tool="list_files", summary=f"Found {len(items)} items", content="\n".join(sorted(items)))
        except Exception as e:
            return ToolResult(ok=False, tool="list_files", summary="List Error", error=str(e))

    def grep_search(self, query: str, path: str = ".") -> ToolResult:
        """全域文字搜尋 (V2 新增)"""
        is_safe, target_path_str = self.constraints.validate_path(path)
        if not is_safe:
            return ToolResult(ok=False, tool="grep_search", summary="Access Denied", error=target_path_str)
        
        try:
            root = Path(target_path_str)
            results = []
            # 遍歷工作區，避開禁止項目
            for p in root.rglob('*'):
                if any(seg in p.parts for seg in self.constraints.forbidden_segments):
                    continue
                if p.is_file() and p.suffix.lower() in self.constraints.allowed_extensions:
                    try:
                        with open(p, 'r', encoding='utf-8', errors='ignore') as f:
                            for i, line in enumerate(f, 1):
                                if query.lower() in line.lower():
                                    results.append(f"{p.relative_to(root)}:{i}: {line.strip()}")
                                if len(results) >= 100: break
                    except: pass
                if len(results) >= 100: break
            
            return ToolResult(ok=True, tool="grep_search", summary=f"Found {len(results)} matches", content="\n".join(results))
        except Exception as e:
            return ToolResult(ok=False, tool="grep_search", summary="Search Error", error=str(e))

    def run_tests(self, path: str = "tests") -> ToolResult:
        """執行單元測試 (V2 新增)"""
        is_safe, target_path_str = self.constraints.validate_path(path)
        if not is_safe:
            return ToolResult(ok=False, tool="run_tests", summary="Access Denied", error=target_path_str)
        
        try:
            # 使用 unittest.TextTestRunner 擷取結果
            loader = unittest.TestLoader()
            suite = loader.discover(target_path_str, pattern="test_*.py")
            stream = io.StringIO()
            runner = unittest.TextTestRunner(stream=stream, verbosity=2)
            result = runner.run(suite)
            
            output = stream.getvalue()
            summary = f"Tests: {result.testsRun}, Failures: {len(result.failures)}, Errors: {len(result.errors)}"
            return ToolResult(ok=result.wasSuccessful(), tool="run_tests", summary=summary, content=output)
        except Exception as e:
            return ToolResult(ok=False, tool="run_tests", summary="Test Execution Error", error=str(e))

    def execute_shell(self, command: str) -> ToolResult:
        return ToolResult(ok=False, tool="execute_shell", summary="Disabled", error="Shell is DISABLED.")

    def write_file(self, path: str, content: str) -> ToolResult:
        return ToolResult(ok=False, tool="write_file", summary="Disabled", error="Writing is DISABLED.")
