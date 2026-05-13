import unittest
from pathlib import Path


class TestDashboardFilesApi(unittest.TestCase):
    def setUp(self):
        self.workspace = Path("tests/dashboard_files_workspace").resolve()
        self.workspace.mkdir(parents=True, exist_ok=True)
        (self.workspace / "README.md").write_text("# Hermes\n", encoding="utf-8")
        (self.workspace / "nested").mkdir(exist_ok=True)
        (self.workspace / "nested" / "note.txt").write_text("hello", encoding="utf-8")
        (self.workspace / ".env").write_text("SECRET=1", encoding="utf-8")

    def tearDown(self):
        pass

    def test_list_workspace_files_filters_forbidden_entries(self):
        from hermes.api.files import list_workspace_files

        result = list_workspace_files(self.workspace, ".")

        self.assertTrue(result["ok"])
        names = [item["name"] for item in result["items"]]
        self.assertIn("README.md", names)
        self.assertIn("nested", names)
        self.assertNotIn(".env", names)

    def test_read_workspace_file_returns_text_content(self):
        from hermes.api.files import read_workspace_file

        result = read_workspace_file(self.workspace, "README.md")

        self.assertTrue(result["ok"])
        self.assertEqual(result["path"], "README.md")
        self.assertEqual(result["content"], "# Hermes\n")

    def test_read_workspace_file_denies_path_escape_with_diagnostic_error(self):
        from hermes.api.files import read_workspace_file

        result = read_workspace_file(self.workspace, "../outside.txt")

        self.assertFalse(result["ok"])
        self.assertEqual(result["error"]["code"], "PATH_DENIED")
        self.assertIn("outside workspace", result["error"]["message"])

    def test_start_hermes_declares_file_api_routes(self):
        source = Path("start_hermes.py").read_text(encoding="utf-8")

        self.assertIn("/api/files/list", source)
        self.assertIn("/api/files/read", source)

    def test_fastapi_server_declares_file_read_route(self):
        source = Path("hermes/api/server.py").read_text(encoding="utf-8")

        self.assertIn('@app.get("/api/files/read")', source)


if __name__ == "__main__":
    unittest.main()
