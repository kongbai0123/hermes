import difflib
from typing import List
from hermes.harness.patch import PatchProposal, FileChange

class DiffEngine:
    """
    Diff 產生器：負責產生成為受控變更的視覺化依據。
    """
    @staticmethod
    def generate_file_diff(change: FileChange) -> str:
        if change.operation == "create":
            return f"--- /dev/null\n+++ {change.path}\n@@ -0,0 +1,1 @@\n+{change.replacement}"
        
        if change.operation == "modify":
            original_lines = (change.original or "").splitlines(keepends=True)
            replacement_lines = (change.replacement or "").splitlines(keepends=True)
            
            diff = difflib.unified_diff(
                original_lines,
                replacement_lines,
                fromfile=f"a/{change.path}",
                tofile=f"b/{change.path}",
                lineterm=""
            )
            return "".join(list(diff))
        
        return ""

    @classmethod
    def generate_patch_diff(cls, proposal: PatchProposal) -> str:
        full_diff = []
        for change in proposal.changes:
            full_diff.append(f"File: {change.path} ({change.operation})")
            full_diff.append(cls.generate_file_diff(change))
            full_diff.append("-" * 40)
        return "\n".join(full_diff)
