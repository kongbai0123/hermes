import unittest
from pathlib import Path


class TestDashboardInteractions(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = Path("hermes/api/dashboard.html").read_text(encoding="utf-8")

    def test_system_prompt_is_persisted_and_clearable(self):
        self.assertIn("hermes_system_prompt", self.html)
        self.assertIn("saveSystemPrompt", self.html)
        self.assertIn("clearSystemPrompt", self.html)

    def test_task_input_is_cleared_after_submit(self):
        self.assertIn("taskInput.value = ''", self.html)
        self.assertIn("taskInput.focus()", self.html)

    def test_managed_agent_trace_components_are_present(self):
        self.assertIn("cursor: pointer", self.html)
        self.assertIn("permission-badge", self.html)
        self.assertIn("MODE: MANAGED_AGENT", self.html)
        self.assertIn("trace-timeline", self.html)
        self.assertIn("renderTraceTimeline", self.html)
        self.assertIn("tool-result-preview", self.html)
        self.assertIn("renderToolResultPreview", self.html)

    def test_redundant_empty_or_native_titles_are_removed(self):
        self.assertNotIn('title=""', self.html)
        self.assertNotIn('title="Refresh dashboard"', self.html)

    def test_reply_and_preview_regions_use_global_scroll_model(self):
        self.assertIn(".agent-reply-body", self.html)
        self.assertIn("overflow-y: visible", self.html)
        self.assertIn("Remove max-height to allow global scroll", self.html)
        self.assertIn(".message-stream", self.html)
        self.assertIn("overflow-y: auto", self.html)
        self.assertIn("body.className = 'agent-reply-body'", self.html)

    def test_dashboard_uses_reply_first_managed_workspace_layout(self):
        self.assertIn("command-bar", self.html)
        self.assertIn("managed-workspace", self.html)
        self.assertIn("reply-panel", self.html)
        self.assertIn("management-panel", self.html)
        self.assertIn("detail-tabs", self.html)
        self.assertIn('data-tab="trace"', self.html)
        self.assertIn('data-tab="tool"', self.html)
        self.assertIn('data-tab="patch"', self.html)
        self.assertIn('data-tab="files"', self.html)
        self.assertIn('data-tab="logs"', self.html)

    def test_dashboard_has_mcp_detail_tab_and_renderer(self):
        self.assertIn('data-tab="mcp"', self.html)
        self.assertIn('id="detail-mcp"', self.html)
        self.assertIn("renderMcpPreview", self.html)
        self.assertIn("MCP_SERVER_READY", self.html)
        self.assertIn("MCP_TOOL_REGISTERED", self.html)

    def test_dashboard_has_shell_approval_panel(self):
        self.assertIn('data-tab="shell"', self.html)
        self.assertIn('id="detail-shell"', self.html)
        self.assertIn("renderShellApprovalPanel", self.html)
        self.assertIn("/api/shell/pending", self.html)
        self.assertIn("/api/shell/approve/", self.html)
        self.assertIn("/api/shell/execute", self.html)

    def test_real_model_is_default_and_mock_is_labeled_as_flow_test(self):
        self.assertIn('<option value="qwen3:14b" selected>Qwen3 14B (Ollama)</option>', self.html)
        self.assertIn('<option value="mock">Mock Demo (UI流程測試，非真實回答)</option>', self.html)
        self.assertIn("Mock Demo (流程測試)", self.html)
        self.assertIn("advanced-settings", self.html)

    def test_dashboard_restores_last_reply_on_initial_load(self):
        self.assertIn(
            "setInterval(checkForPendingPatches, 4000);\n        updateLogs();\n        updateDashboard({ renderResult: true });",
            self.html
        )


if __name__ == "__main__":
    unittest.main()
