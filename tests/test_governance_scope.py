import unittest
import time
from hermes.harness.governance import GovernanceManager

class TestGovernanceScope(unittest.TestCase):
    def setUp(self):
        self.governance = GovernanceManager()

    def test_scoped_grant_authorizes_matching_scope(self):
        patch_id = "patch-abc-123"
        self.governance.grant_scoped_permission(
            "filesystem_write", 
            scope_type="patch", 
            scope_id=patch_id, 
            ttl_seconds=10
        )
        
        self.assertTrue(self.governance.is_authorized("filesystem_write", "patch", patch_id))

    def test_scoped_grant_rejects_wrong_patch_id(self):
        self.governance.grant_scoped_permission(
            "filesystem_write", 
            scope_type="patch", 
            scope_id="patch-A", 
            ttl_seconds=10
        )
        
        self.assertFalse(self.governance.is_authorized("filesystem_write", "patch", "patch-B"))

    def test_scoped_grant_expires(self):
        patch_id = "patch-fast"
        # 授權 1 秒
        self.governance.grant_scoped_permission(
            "filesystem_write", 
            scope_type="patch", 
            scope_id=patch_id, 
            ttl_seconds=1
        )
        
        self.assertTrue(self.governance.is_authorized("filesystem_write", "patch", patch_id))
        
        time.sleep(1.1)
        self.assertFalse(self.governance.is_authorized("filesystem_write", "patch", patch_id))

    def test_global_grant_backward_compatibility(self):
        self.governance.grant_permission("network_access")
        # 全域授權應該對任何 scope 都有效 (或不指定 scope)
        self.assertTrue(self.governance.is_authorized("network_access"))
        self.assertTrue(self.governance.is_authorized("network_access", "any", "thing"))

    def test_revoke_scoped_permission(self):
        pid = "patch-to-revoke"
        self.governance.grant_scoped_permission("filesystem_write", "patch", pid)
        self.assertTrue(self.governance.is_authorized("filesystem_write", "patch", pid))
        
        self.governance.revoke_scoped_permission("filesystem_write", "patch", pid)
        self.assertFalse(self.governance.is_authorized("filesystem_write", "patch", pid))

if __name__ == "__main__":
    unittest.main()
