import unittest
from pathlib import Path


class TestDashboardWorkbenchUI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dashboard = Path("hermes/api/dashboard.html").read_text(encoding="utf-8")
        cls.api_js = Path("hermes/api/static/api.js").read_text(encoding="utf-8")
        cls.renderers_js = Path("hermes/api/static/renderers.js").read_text(encoding="utf-8")

    def test_chat_composer_matches_agent_workbench_contract(self):
        self.assertIn("Message Hermes Agent...", self.dashboard)
        self.assertIn("composer-iconbar", self.dashboard)
        self.assertIn("aria-label=\"Send message\"", self.dashboard)
        self.assertIn("advanced-settings", self.dashboard)
        self.assertIn("default", self.dashboard)
        self.assertIn("Home", self.dashboard)
        self.assertNotIn('<span class="control-btn">Mock Demo (流程測試)</span>', self.dashboard)

    def test_workspace_tabs_hide_scrollbar_and_support_wheel_scroll(self):
        self.assertIn("scrollbar-width: none", self.dashboard)
        self.assertIn(".workspace-tabs::-webkit-scrollbar", self.dashboard)
        self.assertIn("bindHorizontalWheelScroll", self.dashboard)
        self.assertIn("deltaY", self.dashboard)

    def test_sidebar_replaces_placeholder_tools_with_management_roles(self):
        self.assertIn("Management Decision Layer", self.dashboard)
        for role in ["Executive", "Strategy", "Operator", "Auditor"]:
            self.assertIn(f'data-role="{role.lower()}"', self.dashboard)

        self.assertNotIn("<span>📁</span> Projects", self.dashboard)
        self.assertNotIn("<span>⚡</span> Skills", self.dashboard)
        self.assertNotIn("<span>⚙️</span> Settings", self.dashboard)

    def test_left_sidebar_actions_are_functional(self):
        self.assertIn("startNewChat()", self.dashboard)
        self.assertIn("openToolBox('search')", self.dashboard)
        self.assertIn("openToolBox('extensions')", self.dashboard)
        self.assertIn("openToolBox('automation')", self.dashboard)
        self.assertIn("openUserSettings()", self.dashboard)
        self.assertIn("New Chat", self.dashboard)
        self.assertIn("Search", self.dashboard)
        self.assertIn("Extensions", self.dashboard)
        self.assertIn("Automations", self.dashboard)
        self.assertIn("User Settings", self.dashboard)

    def test_history_items_load_session_content(self):
        self.assertIn("loadSession(", self.dashboard)
        self.assertIn("SESSION_CONTENT", self.dashboard)
        self.assertIn("data-session=", self.dashboard)
        self.assertIn("renderSessionHistory", self.dashboard)

    def test_module_rail_buttons_have_real_actions(self):
        self.assertIn("bindModuleRailActions", self.dashboard)
        self.assertIn("openModuleTool", self.dashboard)
        self.assertIn("data-module=\"chat\"", self.dashboard)

    def test_left_rail_contains_modules_and_history_groups(self):
        for module in ["Chat", "Calendar", "Layers", "Memory", "Files", "Profile", "Queue"]:
            self.assertIn(f'data-module="{module.lower()}"', self.dashboard)

        for group in ["PINNED", "TODAY", "EARLIER"]:
            self.assertIn(group, self.dashboard)

    def test_mcp_panel_uses_card_contract_not_raw_text_only(self):
        self.assertIn("mcp-server-list", self.dashboard)
        self.assertIn("mcp-tool-list", self.dashboard)
        self.assertIn("mcp-call-list", self.dashboard)
        self.assertIn("mcp-status-card", self.renderers_js)
        self.assertIn("Recent MCP Calls", self.renderers_js)

    def test_api_reports_html_fallback_as_diagnostic_error(self):
        self.assertIn("API returned HTML", self.api_js)
        self.assertIn("restart Hermes", self.api_js)
        self.assertIn("content-type", self.api_js.lower())
        self.assertIn("API_ENDPOINTS", self.api_js)
        self.assertIn("requestFirstJson", self.api_js)

    def test_send_task_handles_success_and_loading_state(self):
        self.assertIn("appendAgentProgress", self.dashboard)
        self.assertIn("updateAgentProgress", self.dashboard)
        self.assertIn("Hermes is reading", self.dashboard)
        self.assertIn("payload.result", self.dashboard)
        self.assertNotIn("System Error: ${res.detail}", self.dashboard)

    def test_user_settings_include_ai_preferences_and_enter_mode(self):
        self.assertIn("AI Preferences", self.dashboard)
        self.assertIn("User Rules", self.dashboard)
        self.assertIn("send-mode", self.dashboard)
        self.assertIn("Enter to send", self.dashboard)
        self.assertIn("Ctrl+Enter to send", self.dashboard)
        self.assertIn("handleComposerKeydown", self.dashboard)


if __name__ == "__main__":
    unittest.main()
