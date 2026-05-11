from pathlib import Path
import unittest
import io
from typing import Optional, Any, List, Dict
from hermes.harness.constraints import ConstraintValidator
from hermes.core.types import ToolResult
from hermes.harness.patch import PatchProposal, FileChange
from hermes.harness.diff_engine import DiffEngine
from hermes.harness.approval import ApprovalManager

class SafeExecutor:
    """
    安全執行器 V2.2: 具備 Patch 治理能力的 L3-α 執行環境。
    """
    def __init__(self, constraints: ConstraintValidator):
        self.constraints = constraints
        self.max_read_chars = 12000
        self.approval_manager = ApprovalManager()
        self.diff_engine = DiffEngine()

    # --- 唯讀工具 (V1/V2.1) ---
    def read_file(self, path: str, max_chars: Optional[int] = None) -> ToolResult:
        limit = max_chars or self.max_read_chars
        is_safe, target_path_str = self.constraints.validate_path(path)
        if not is_safe:
            return ToolResult(ok=False, tool="read_file", summary="Access Denied", error=target_path_str)
        try:
            target_path = Path(target_path_str)
            if not target_path.is_file():
                return ToolResult(ok=False, tool="read_file", summary="Not a file", error="Target is not a file.")
            with open(target_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read(limit + 1)
            return ToolResult(ok=True, tool="read_file", summary="Read success", content=content[:limit])
        except Exception as e:
            return ToolResult(ok=False, tool="read_file", summary="Read Error", error=str(e))

    def list_files(self, path: str = ".") -> ToolResult:
        is_safe, target_path_str = self.constraints.validate_path(path)
        if not is_safe:
            return ToolResult(ok=False, tool="list_files", summary="Access Denied", error=target_path_str)
        try:
            items = [f"{'[D] ' if i.is_dir() else '[F] '}{i.name}" for i in list(Path(target_path_str).iterdir())]
            return ToolResult(ok=True, tool="list_files", summary="List success", content="\n".join(items))
        except Exception as e:
            return ToolResult(ok=False, tool="list_files", summary="List Error", error=str(e))

    def grep_search(self, query: str, path: str = ".") -> ToolResult:
        is_safe, target_path_str = self.constraints.validate_path(path)
        if not is_safe: return ToolResult(ok=False, tool="grep_search", summary="Access Denied", error=target_path_str)
        results = []
        try:
            root = Path(target_path_str)
            for p in root.rglob('*'):
                if any(seg in p.parts for seg in self.constraints.forbidden_segments): continue
                if p.is_file() and p.suffix.lower() in self.constraints.allowed_extensions:
                    with open(p, 'r', encoding='utf-8', errors='ignore') as f:
                        for i, line in enumerate(f, 1):
                            if query.lower() in line.lower():
                                results.append(f"{p.relative_to(root)}:{i}: {line.strip()}")
                if len(results) >= 100: break
            return ToolResult(ok=True, tool="grep_search", summary=f"Found {len(results)} matches", content="\n".join(results))
        except Exception as e: return ToolResult(ok=False, tool="grep_search", summary="Error", error=str(e))

    # --- 治理工具 (V2.2) ---
    def propose_patch(self, task: str, changes: List[Dict[str, Any]]) -> ToolResult:
        """
        提出 Patch 提議：將變更暫存在記憶體中，並產生 Diff。
        """
        try:
            file_changes = []
            for c in changes:
                path = c["path"]
                is_safe, target_path_str = self.constraints.validate_path(path)
                if not is_safe:
                    return ToolResult(ok=False, tool="propose_patch", summary="Access Denied", error=target_path_str)
                
                original_content = ""
                if c["operation"] == "modify":
                    with open(target_path_str, 'r', encoding='utf-8') as f:
                        original_content = f.read()
                
                file_changes.append(FileChange(
                    path=path,
                    operation=c["operation"],
                    reason=c.get("reason", ""),
                    original=original_content,
                    replacement=c.get("replacement", "")
                ))
            
            proposal = PatchProposal(task_id=task, changes=file_changes)
            self.approval_manager.register_proposal(proposal)
            
            diff = self.diff_engine.generate_patch_diff(proposal)
            return ToolResult(
                ok=True, 
                tool="propose_patch", 
                summary=f"Proposal {proposal.id} created. Approval REQUIRED.",
                content=diff,
                metadata={"patch_id": proposal.id}
            )
        except Exception as e:
            return ToolResult(ok=False, tool="propose_patch", summary="Proposal Failed", error=str(e))

    def apply_approved_patch(self, patch_id: str, approval_token: str) -> ToolResult:
        """
        套用已授權的 Patch：執行實體寫入。
        """
        if not self.approval_manager.validate(patch_id, approval_token):
            return ToolResult(ok=False, tool="apply_approved_patch", summary="Unauthorized", error="Invalid or expired token.")
        
        proposal = self.approval_manager.pending_patches.get(patch_id)
        results = []
        try:
            for change in proposal.changes:
                is_safe, target_path_str = self.constraints.validate_path(change.path)
                if not is_safe:
                    return ToolResult(ok=False, tool="apply_approved_patch", summary="Safety Violation during apply", error=target_path_str)
                
                target_path = Path(target_path_str)
                if change.operation == "modify" or change.operation == "create":
                    # 確保目錄存在
                    target_path.parent.mkdir(parents=True, exist_ok=True)
                    with open(target_path, 'w', encoding='utf-8') as f:
                        f.write(change.replacement)
                elif change.operation == "delete":
                    if target_path.exists(): target_path.unlink()
                
                results.append(f"Applied: {change.path}")
            
            proposal.status = "applied"
            return ToolResult(ok=True, tool="apply_approved_patch", summary=f"Patch {patch_id} applied successfully.", content="\n".join(results))
        except Exception as e:
            proposal.status = "failed"
            return ToolResult(ok=False, tool="apply_approved_patch", summary="Apply Failed", error=str(e))

    def run_tests(self, path: str = "tests") -> ToolResult:
        is_safe, target_path_str = self.constraints.validate_path(path)
        if not is_safe: return ToolResult(ok=False, tool="run_tests", summary="Access Denied", error=target_path_str)
        try:
            loader = unittest.TestLoader()
            suite = loader.discover(target_path_str, pattern="test_*.py")
            stream = io.StringIO()
            runner = unittest.TextTestRunner(stream=stream, verbosity=2)
            result = runner.run(suite)
            return ToolResult(ok=result.wasSuccessful(), tool="run_tests", summary=f"Tests: {result.testsRun}, Fail: {len(result.failures)}", content=stream.getvalue())
        except Exception as e: return ToolResult(ok=False, tool="run_tests", summary="Error", error=str(e))

    def execute_shell(self, command: str) -> ToolResult:
        return ToolResult(ok=False, tool="execute_shell", summary="Disabled", error="Shell is DISABLED.")
