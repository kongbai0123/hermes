import unittest
import os
from pathlib import Path
from hermes.harness.constraints import ConstraintValidator
from hermes.harness.executor import SafeExecutor
from hermes.core.types import ToolResult

class TestSafeExecutor(unittest.TestCase):
    def setUp(self):
        # 建立測試工作區
        self.test_root = Path("e:/program/hermes/tests/temp_workspace").resolve()
        self.test_root.mkdir(parents=True, exist_ok=True)
        (self.test_root / "test.txt").write_text("Hello Hermes", encoding='utf-8')
        (self.test_root / ".env").write_text("SECRET=123", encoding='utf-8')
        
        # 初始化
        self.constraints = ConstraintValidator(workspace_root=str(self.test_root))
        self.executor = SafeExecutor(self.constraints)

    def test_read_file_success(self):
        result = self.executor.read_file(path="test.txt")
        self.assertTrue(result.ok)
        self.assertEqual(result.content, "Hello Hermes")

    def test_list_files_success(self):
        result = self.executor.list_files(path=".")
        self.assertTrue(result.ok)
        self.assertIn("[F] test.txt", result.content)

    def test_boundary_violation(self):
        # 嘗試讀取外部
        result = self.executor.read_file(path="../../start_hermes.py")
        self.assertFalse(result.ok)
        self.assertIn("outside workspace boundary", result.error)

    def test_sensitive_file_blocked(self):
        result = self.executor.read_file(path=".env")
        self.assertFalse(result.ok)
        self.assertIn("Forbidden", result.error)

if __name__ == '__main__':
    unittest.main()
