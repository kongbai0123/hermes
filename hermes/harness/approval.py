import time
import secrets
import hashlib
from typing import Dict, Optional
from hermes.harness.patch import PatchProposal

class ApprovalManager:
    """
    授權管理員：負責核發與查驗 Patch 執行權限。
    """
    def __init__(self, expiration_seconds: int = 300):
        self.pending_patches: Dict[str, PatchProposal] = {}
        self.tokens: Dict[str, Dict] = {}
        self.expiration_seconds = expiration_seconds

    def register_proposal(self, proposal: PatchProposal):
        self.pending_patches[proposal.id] = proposal

    def approve(self, patch_id: str) -> Optional[str]:
        if patch_id not in self.pending_patches:
            return None
        
        proposal = self.pending_patches[patch_id]
        token = secrets.token_hex(16)
        
        self.tokens[token] = {
            "patch_id": patch_id,
            "patch_hash": self._hash_proposal(proposal),
            "expires_at": time.time() + self.expiration_seconds
        }
        proposal.status = "approved"
        return token

    def validate(self, patch_id: str, token: str) -> bool:
        if token not in self.tokens:
            return False
        if patch_id not in self.pending_patches:
            return False
        
        record = self.tokens[token]
        if record["patch_id"] != patch_id:
            return False
            
        if time.time() > record["expires_at"]:
            return False

        proposal = self.pending_patches[patch_id]
        if record.get("patch_hash") != self._hash_proposal(proposal):
            return False
            
        return True

    def _hash_proposal(self, proposal: PatchProposal) -> str:
        parts = [proposal.id, proposal.task_id]
        for change in proposal.changes:
            parts.extend([
                change.path,
                change.operation,
                change.before_hash or "",
                change.replacement or "",
            ])
        data = "|".join(parts)
        return hashlib.sha256(data.encode()).hexdigest()
