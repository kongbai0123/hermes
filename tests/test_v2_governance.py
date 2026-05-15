import unittest
from pathlib import Path
from hermes.harness.constraints import ConstraintValidator
from hermes.harness.patch import PatchProposal, FileChange
from hermes.harness.diff_engine import DiffEngine
from hermes.harness.approval import ApprovalManager
from tests.support import repo_root

class TestGovernance(unittest.TestCase):
    def setUp(self):
        self.workspace = repo_root()
        self.constraints = ConstraintValidator(workspace_root=str(self.workspace))

    def test_strict_path_boundary(self):
        # 1. 正常路徑
        is_safe, _ = self.constraints.validate_path("hermes/core/runtime.py")
        self.assertTrue(is_safe)

        # 2. 偽裝路徑 (hermes_backup 曾是 startswith 的漏洞)
        # 注意: 這裡我們假設系統中可能存在這個目錄，但它不屬於 workspace
        is_safe, _ = self.constraints.validate_path("../hermes_backup/secret.txt")
        self.assertFalse(is_safe)

    def test_diff_generation(self):
        change = FileChange(
            path="hello.py",
            operation="modify",
            reason="update greeting",
            original="print('hello')\n",
            replacement="print('hello world')\n"
        )
        diff = DiffEngine.generate_file_diff(change)
        self.assertIn("-print('hello')", diff)
        self.assertIn("+print('hello world')", diff)

    def test_approval_flow(self):
        manager = ApprovalManager(expiration_seconds=1)
        proposal = PatchProposal(task_id="T1", changes=[])
        manager.register_proposal(proposal)
        
        # 核發 Token
        token = manager.approve(proposal.id)
        self.assertIsNotNone(token)
        
        # 驗證 Token
        self.assertTrue(manager.validate(proposal.id, token))
        
        # 驗證錯誤 ID
        self.assertFalse(manager.validate("WRONG_ID", token))

if __name__ == '__main__':
    unittest.main()
