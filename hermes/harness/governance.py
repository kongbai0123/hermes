import time
from typing import Dict, Any, List, Optional

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

    def is_authorized(self, action_type: str) -> bool:
        return self.permissions.get(action_type, False)
