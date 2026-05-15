import unittest
import os
from pathlib import Path
from hermes.harness.constraints import ConstraintValidator
from hermes.harness.executor import SafeExecutor
from hermes.core.types import ToolResult
from tests.support import repo_root, test_workspace

class TestSafeExecutor(unittest.TestCase):
    def setUp(self):
        # 建立測試工作區
        self.test_root = test_workspace("temp_workspace").resolve()
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

    def test_explicit_workspace_root_takes_priority_over_environment(self):
        os.environ["HERMES_WORKSPACE"] = str(repo_root())
        try:
            constraints = ConstraintValidator(workspace_root=str(self.test_root))
            self.assertEqual(constraints.workspace_root, self.test_root)
        finally:
            os.environ.pop("HERMES_WORKSPACE", None)

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
        self.assertIn("Access Denied", result.error)

    def test_generate_design_artifact_returns_structured_content_without_writing(self):
        result = self.executor.generate_design_artifact(goal="製作一個簡潔的個人作品集網站")

        self.assertTrue(result.ok)
        self.assertIn("生成目標", result.content)
        self.assertIn("個人作品集網站", result.content)
        self.assertIn("安全邊界", result.content)
        self.assertFalse((self.test_root / "index.html").exists())

    def test_create_project_workspace_creates_isolated_user_project(self):
        result = self.executor.create_project_workspace(
            name="demo-site",
            brief="製作一個首頁設計",
        )

        project_dir = self.test_root / "user_projects" / "demo-site"
        self.assertTrue(result.ok)
        self.assertTrue(project_dir.is_dir())
        self.assertTrue((project_dir / "README.md").is_file())
        self.assertTrue((project_dir / "design_brief.md").is_file())
        self.assertIn("user_projects/demo-site", result.content.replace("\\", "/"))
        self.assertIn("demo-site", result.metadata["path"])

    def test_generate_static_site_writes_html_and_css_inside_user_project(self):
        result = self.executor.generate_static_site(
            name="minimal-site",
            brief="建立簡約風本地網站",
        )

        project_dir = self.test_root / "user_projects" / "minimal-site"
        self.assertTrue(result.ok)
        self.assertTrue((project_dir / "index.html").is_file())
        self.assertTrue((project_dir / "styles.css").is_file())
        self.assertIn("index.html", result.content)
        self.assertIn("styles.css", result.content)
        self.assertIn("minimal-site", result.metadata["path"])

if __name__ == '__main__':
    unittest.main()
