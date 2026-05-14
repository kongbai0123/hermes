import unittest
import os
from pathlib import Path
from hermes.harness.constraints import ConstraintValidator
from hermes.harness.executor import SafeExecutor
from tests.support import test_workspace

class TestV2Tools(unittest.TestCase):
    def setUp(self):
        # 建立測試環境
        self.test_root = test_workspace("v2_test_workspace").resolve()
        self.test_root.mkdir(parents=True, exist_ok=True)
        (self.test_root / "test_file.py").write_text("print('hermes_v2_secret')", encoding='utf-8')
        (self.test_root / "other.txt").write_text("nothing here", encoding='utf-8')
        
        # 建立子目錄測試
        (self.test_root / "subdir").mkdir(exist_ok=True)
        (self.test_root / "subdir" / "test_inner.py").write_text("def test_me(): pass", encoding='utf-8')

        self.constraints = ConstraintValidator(workspace_root=str(self.test_root))
        self.executor = SafeExecutor(self.constraints)

    def test_grep_search_success(self):
        # 搜尋存在的關鍵字
        result = self.executor.grep_search(query="hermes_v2_secret", path=".")
        self.assertTrue(result.ok)
        self.assertIn("test_file.py:1", result.content)
        self.assertIn("hermes_v2_secret", result.content)

    def test_grep_search_no_match(self):
        # 搜尋不存在的關鍵字
        result = self.executor.grep_search(query="nonexistent_xyz", path=".")
        self.assertTrue(result.ok)
        self.assertEqual(result.content, "")

    def test_run_tests_execution(self):
        # 執行臨時工作區內的測試 (雖然目前沒有測試檔，但應該返回成功的 0 測試結果)
        result = self.executor.run_tests(path=".")
        self.assertIn("Tests:", result.summary)
        self.assertTrue(result.ok)

if __name__ == '__main__':
    unittest.main()
