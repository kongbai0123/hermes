import time
from dataclasses import dataclass
from typing import Dict, Any, List, Optional

@dataclass
class PermissionGrant:
    permission: str
    scope_type: Optional[str] = None
    scope_id: Optional[str] = None
    expires_at: Optional[float] = None
    granted_by: str = "user"

class GovernanceManager:
    """
    治理層: 負責預算控制、權限審核與上下文邊界保護。
    """
    def __init__(self, token_budget: int = 100000, time_budget_sec: int = 3600):
        self.token_budget = token_budget
        self.time_budget_sec = time_budget_sec
        self.consumed_tokens = 0
        self.start_time = time.time()
        self.permissions: Dict[str, bool] = {
            "filesystem_write": False,
            "network_access": False,
            "shell_execute": False
        }
        self.scoped_grants: List[PermissionGrant] = []

    def check_budget(self) -> bool:
        elapsed_time = time.time() - self.start_time
        if self.consumed_tokens > self.token_budget:
            return False
        if elapsed_time > self.time_budget_sec:
            return False
        return True

    def update_usage(self, tokens: int):
        self.consumed_tokens += tokens

    def grant_permission(self, permission: str):
        if permission in self.permissions:
            self.permissions[permission] = True
            print(f"[Governance] Permission GRANTED: {permission}")

    def revoke_permission(self, permission: str):
        if permission in self.permissions:
            self.permissions[permission] = False
            print(f"[Governance] Permission REVOKED: {permission}")

    def is_authorized(self, action_type: str, scope_type: Optional[str] = None, scope_id: Optional[str] = None) -> bool:
        # 1. 檢查全域權限 (向下相容)
        if self.permissions.get(action_type, False):
            return True
            
        # 2. 檢查 Scoped 權限
        self.cleanup_expired_grants()
        for grant in self.scoped_grants:
            if grant.permission == action_type:
                if scope_type and grant.scope_type != scope_type:
                    continue
                if scope_id and grant.scope_id != scope_id:
                    continue
                
                # 如果有指定 scope 但 grant 是全域的 (scope 為空)，或者 scope 完全匹配
                if (not scope_type or grant.scope_type == scope_type) and \
                   (not scope_id or grant.scope_id == scope_id):
                    return True
        return False

    def grant_scoped_permission(self, permission: str, scope_type: str, scope_id: str, ttl_seconds: int = 60, granted_by: str = "user"):
        expires_at = time.time() + ttl_seconds
        grant = PermissionGrant(
            permission=permission,
            scope_type=scope_type,
            scope_id=scope_id,
            expires_at=expires_at,
            granted_by=granted_by
        )
        self.scoped_grants.append(grant)
        print(f"[Governance] Scoped Grant: {permission} for {scope_type}:{scope_id} (TTL: {ttl_seconds}s)")

    def revoke_scoped_permission(self, permission: str, scope_type: str, scope_id: str):
        self.scoped_grants = [
            g for g in self.scoped_grants 
            if not (g.permission == permission and g.scope_type == scope_type and g.scope_id == scope_id)
        ]
        print(f"[Governance] Scoped Revoked: {permission} for {scope_type}:{scope_id}")

    def cleanup_expired_grants(self):
        now = time.time()
        initial_count = len(self.scoped_grants)
        self.scoped_grants = [g for g in self.scoped_grants if g.expires_at is None or g.expires_at > now]
        if len(self.scoped_grants) < initial_count:
            print(f"[Governance] Cleaned up {initial_count - len(self.scoped_grants)} expired grants")
