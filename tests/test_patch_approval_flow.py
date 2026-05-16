import unittest
import os
import shutil
from pathlib import Path
from hermes.harness.executor import SafeExecutor
from hermes.harness.constraints import ConstraintValidator
from hermes.harness.governance import GovernanceManager

class TestPatchApprovalFlow(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path("tests/tmp_patch_flow").resolve()
        self.test_dir.mkdir(parents=True, exist_ok=True)
        self.constraints = ConstraintValidator(workspace_root=str(self.test_dir))
        self.governance = GovernanceManager()
        self.executor = SafeExecutor(self.constraints, governance=self.governance)

    def tearDown(self):
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def test_full_patch_approval_flow_with_scoped_grant(self):
        # 1. 準備一個檔案
        target_file = self.test_dir / "app.py"
        target_file.write_text("print('hello')", encoding='utf-8')
        
        # 2. 提出 Patch
        changes = [{
            "path": str(target_file),
            "operation": "modify",
            "reason": "Update greeting",
            "replacement": "print('hello world')"
        }]
        proposal_result = self.executor.propose_patch(task="Update app", changes=changes)
        self.assertTrue(proposal_result.ok)
        patch_id = proposal_result.metadata["patch_id"]
        
        # 3. 嘗試在未授權時套用 (應被 Governance Blocked)
        # 注意：雖然有 token，但沒有 governance scoped grant
        token = self.executor.approval_manager.approve(patch_id)
        apply_fail = self.executor.apply_approved_patch(patch_id, token)
        self.assertFalse(apply_fail.ok)
        self.assertIn("Governance Blocked", apply_fail.summary)
        
        # 4. 授予 Scoped 權限
        self.governance.grant_scoped_permission("filesystem_write", "patch", patch_id)
        
        # 5. 正確套用
        apply_success = self.executor.apply_approved_patch(patch_id, token)
        self.assertTrue(apply_success.ok)
        self.assertEqual(target_file.read_text(encoding='utf-8'), "print('hello world')")
        
        # 6. 模擬 Revoke (API 層負責，這裡手動模擬)
        self.governance.revoke_scoped_permission("filesystem_write", "patch", patch_id)
        self.assertFalse(self.governance.is_authorized("filesystem_write", "patch", patch_id))

    def test_wrong_patch_id_cannot_use_others_grant(self):
        # 建立兩個 Patch
        p1_res = self.executor.propose_patch("T1", [{"path": str(self.test_dir/"1.txt"), "operation": "create", "replacement": "1"}])
        p2_res = self.executor.propose_patch("T2", [{"path": str(self.test_dir/"2.txt"), "operation": "create", "replacement": "2"}])
        
        pid1 = p1_res.metadata["patch_id"]
        pid2 = p2_res.metadata["patch_id"]
        
        # 只授權給 Patch 1
        self.governance.grant_scoped_permission("filesystem_write", "patch", pid1)
        
        # 嘗試套用 Patch 2 (即便有 token 也不行)
        token2 = self.executor.approval_manager.approve(pid2)
        apply2 = self.executor.apply_approved_patch(pid2, token2)
        
    def test_global_grant_cannot_bypass_patch_scoped_check(self):
        # 1. 準備 Patch
        p_res = self.executor.propose_patch("T3", [{"path": str(self.test_dir/"3.txt"), "operation": "create", "replacement": "3"}])
        pid = p_res.metadata["patch_id"]
        token = self.executor.approval_manager.approve(pid)
        
        # 2. 授予全域權限 (舊模型)
        self.governance.grant_permission("filesystem_write")
        
        # 3. 嘗試套用 (應被拒絕，因為 apply_approved_patch 使用 scoped check)
        apply_res = self.executor.apply_approved_patch(pid, token)
        self.assertFalse(apply_res.ok)
        self.assertIn(f"NOT authorized for patch_id={pid}", apply_res.error)
        
        # 4. 授予正確的 Scoped 權限後才可套用
        self.governance.grant_scoped_permission("filesystem_write", "patch", pid)
        apply_ok = self.executor.apply_approved_patch(pid, token)
        self.assertTrue(apply_ok.ok)

if __name__ == "__main__":
    unittest.main()
