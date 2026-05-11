import unittest
import os
from pathlib import Path
from hermes.harness.constraints import ConstraintValidator
from hermes.harness.executor import SafeExecutor

class TestPatchFlow(unittest.TestCase):
    def setUp(self):
        # 建立測試沙盒
        self.test_root = Path("e:/program/hermes/tests/patch_test_workspace").resolve()
        self.test_root.mkdir(parents=True, exist_ok=True)
        (self.test_root / "hello.py").write_text("print('old')", encoding='utf-8')
        
        self.constraints = ConstraintValidator(workspace_root=str(self.test_root))
        self.executor = SafeExecutor(self.constraints)

    def test_full_patch_lifecycle(self):
        # 1. Propose
        changes = [{
            "path": "hello.py",
            "operation": "modify",
            "replacement": "print('new')"
        }]
        result = self.executor.propose_patch(task="update greeting", changes=changes)
        self.assertTrue(result.ok)
        patch_id = result.metadata["patch_id"]
        self.assertIn("-print('old')", result.content)
        self.assertIn("+print('new')", result.content)
        
        # 2. 驗證檔案尚未改變 (Read-Only 依然生效)
        self.assertEqual((self.test_root / "hello.py").read_text(), "print('old')")
        
        # 3. Apply without Token (應失敗)
        fail_result = self.executor.apply_approved_patch(patch_id, "WRONG_TOKEN")
        self.assertFalse(fail_result.ok)
        
        # 4. Approve & Get Token
        token = self.executor.approval_manager.approve(patch_id)
        self.assertIsNotNone(token)
        
        # 5. Apply with Correct Token (應成功)
        success_result = self.executor.apply_approved_patch(patch_id, token)
        self.assertTrue(success_result.ok)
        
        # 6. 驗證實體檔案已更新
        self.assertEqual((self.test_root / "hello.py").read_text(), "print('new')")

    def test_create_file_patch(self):
        # 測試建立新檔案的流程
        changes = [{
            "path": "new_module.py",
            "operation": "create",
            "replacement": "def foo(): pass"
        }]
        result = self.executor.propose_patch(task="add module", changes=changes)
        patch_id = result.metadata["patch_id"]
        
        token = self.executor.approval_manager.approve(patch_id)
        self.executor.apply_approved_patch(patch_id, token)
        
        self.assertTrue((self.test_root / "new_module.py").exists())
        self.assertEqual((self.test_root / "new_module.py").read_text(), "def foo(): pass")

if __name__ == '__main__':
    unittest.main()
