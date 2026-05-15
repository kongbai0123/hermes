from dataclasses import dataclass, field
from typing import List, Literal, Optional, Dict
import uuid
import time

@dataclass
class FileChange:
    """單一檔案的原子變更描述"""
    path: str
    operation: Literal["modify", "create"]
    reason: str
    before_hash: Optional[str] = None
    original: Optional[str] = None
    replacement: Optional[str] = None

@dataclass
class PatchProposal:
    """完整的補丁提議包"""
    task_id: str
    changes: List[FileChange]
    risk_level: Literal["low", "medium", "high"] = "low"
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    timestamp: float = field(default_factory=time.time)
    requires_approval: bool = True
    status: Literal["pending", "approved", "applied", "rejected", "failed"] = "pending"

    def get_summary(self) -> str:
        files = [c.path for c in self.changes]
        return f"Patch {self.id}: {len(self.changes)} changes in {', '.join(files)}"
