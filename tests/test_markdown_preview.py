import unittest
from pathlib import Path


class TestMarkdownPreviewDashboard(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dashboard = Path("hermes/api/dashboard.html").read_text(encoding="utf-8")
        cls.markdown_js_path = Path("hermes/api/static/markdown_preview.js")
        cls.markdown_js = cls.markdown_js_path.read_text(encoding="utf-8") if cls.markdown_js_path.exists() else ""

    def test_p0_dashboard_declares_markdown_preview_contract(self):
        self.assertIn("markdown-preview-panel", self.dashboard)
        self.assertIn("markdown-toc-sidebar", self.dashboard)
        self.assertIn("markdown-search-input", self.dashboard)
        self.assertIn("previewFileMode", self.dashboard)
        self.assertIn("renderMarkdownPreview", self.dashboard)
        self.assertIn("toggleMarkdownPreviewMode", self.dashboard)

    def test_p0_markdown_renderer_supports_leaf_like_reading_features(self):
        self.assertTrue(self.markdown_js_path.exists())
        self.assertIn("extractMarkdownToc", self.markdown_js)
        self.assertIn("renderMarkdownPreview", self.markdown_js)
        self.assertIn("renderFrontmatter", self.markdown_js)
        self.assertIn("renderMarkdownTable", self.markdown_js)
        self.assertIn("highlightMarkdownMatches", self.markdown_js)

    def test_p2_dashboard_declares_watch_like_refresh_contract(self):
        self.assertIn("autoRefreshPreview", self.dashboard)
        self.assertIn("schedulePreviewRefresh", self.dashboard)
        self.assertIn("lastPreviewSignature", self.dashboard)
        self.assertIn("HermesApi.statFile", self.dashboard)
        self.assertIn("filesStat", Path("hermes/api/static/api.js").read_text(encoding="utf-8"))


class TestMarkdownPreviewFilesApi(unittest.TestCase):
    def test_p2_file_stat_api_returns_signature(self):
        from hermes.api.files import stat_workspace_file

        result = stat_workspace_file(Path.cwd(), "tests/fixtures/markdown_report.md")

        self.assertTrue(result["ok"])
        self.assertEqual(result["path"], "tests/fixtures/markdown_report.md")
        self.assertIn("mtime", result)
        self.assertIn("signature", result)


if __name__ == "__main__":
    unittest.main()


class TestMarkdownReportTools(unittest.TestCase):
    def test_p1_executor_reads_markdown_report_with_summary_and_toc(self):
        from hermes.harness.constraints import ConstraintValidator
        from hermes.harness.executor import SafeExecutor

        executor = SafeExecutor(ConstraintValidator(workspace_root=str(Path.cwd())))

        result = executor.read_markdown_report("tests/fixtures/markdown_report.md")

        self.assertTrue(result.ok)
        self.assertIn("Daily", result.summary)
        self.assertEqual([item["text"] for item in result.metadata["toc"]], ["Daily", "Status", "Risks"])
        self.assertIn("All tests passed", result.content)

    def test_p1_tool_registry_exposes_markdown_report_tools(self):
        from hermes.harness.constraints import ConstraintValidator
        from hermes.harness.executor import SafeExecutor
        from hermes.harness.tools import ToolRegistry

        registry = ToolRegistry(SafeExecutor(ConstraintValidator()))

        self.assertIsNotNone(registry.get_tool("read_markdown_report"))
        self.assertIsNotNone(registry.get_tool("preview_report"))
        self.assertIsNotNone(registry.get_tool("extract_markdown_toc"))

    def test_p3_leaf_optional_adapter_proposes_read_only_inline_command(self):
        from hermes.harness.constraints import ConstraintValidator
        from hermes.harness.executor import SafeExecutor

        executor = SafeExecutor(ConstraintValidator(workspace_root=str(Path.cwd())))
        result = executor.propose_leaf_inline_preview("tests/fixtures/markdown_report.md")

        self.assertTrue(result.ok)
        self.assertIn("leaf --inline", result.content)
        self.assertIn("tests/fixtures/markdown_report.md", result.content)
        self.assertEqual(result.metadata["permission"], "read")
        self.assertFalse(result.metadata["executes"])

    def test_p3_tool_registry_exposes_leaf_optional_adapter(self):
        from hermes.harness.constraints import ConstraintValidator
        from hermes.harness.executor import SafeExecutor
        from hermes.harness.tools import ToolRegistry

        registry = ToolRegistry(SafeExecutor(ConstraintValidator()))

        tool = registry.get_tool("propose_leaf_inline_preview")
        self.assertIsNotNone(tool)
        self.assertEqual(tool.permission, "write_proposal")

    def test_p4_management_routes_leaf_request_to_proposal(self):
        from hermes.harness.constraints import ConstraintValidator
        from hermes.harness.executor import SafeExecutor
        from hermes.harness.tools import ToolRegistry
        from hermes.management.orchestrator import ManagementOrchestrator

        registry = ToolRegistry(SafeExecutor(ConstraintValidator(workspace_root=str(Path.cwd()))))
        plan = ManagementOrchestrator(registry).plan("請用 Leaf preview README.md")

        self.assertEqual(plan.decision.intent, "leaf_preview")
        self.assertEqual(plan.decision.risk_level, "requires_user_approval")
        self.assertEqual(plan.steps[0].tool, "propose_leaf_inline_preview")
        self.assertEqual(plan.steps[0].args["path"], "README.md")
