import unittest

from hermes.management.policy import ManagementPolicy


class TestManagementPolicy(unittest.TestCase):
    def setUp(self):
        self.policy = ManagementPolicy()

    def test_general_chat_is_low_risk(self):
        decision = self.policy.classify_task("你好，請介紹 Hermes")

        self.assertEqual(decision.intent, "general_chat")
        self.assertEqual(decision.risk_level, "low")
        self.assertFalse(decision.requires_tools)
        self.assertFalse(decision.requires_write)

    def test_read_file_is_low_risk_tool_task(self):
        decision = self.policy.classify_task("請讀取 README.md 並摘要")

        self.assertEqual(decision.intent, "read_workspace")
        self.assertEqual(decision.risk_level, "low")
        self.assertTrue(decision.requires_tools)
        self.assertFalse(decision.requires_write)

    def test_run_tests_is_medium_risk(self):
        decision = self.policy.classify_task("請執行測試")

        self.assertEqual(decision.intent, "run_tests")
        self.assertEqual(decision.risk_level, "medium")
        self.assertTrue(decision.requires_tools)

    def test_mcp_read_request_marks_external_tool_governance(self):
        decision = self.policy.classify_task("請用 MCP 讀取 GitHub issue")

        self.assertEqual(decision.intent, "mcp_read")
        self.assertTrue(decision.requires_tools)
        self.assertFalse(decision.requires_write)
        self.assertTrue(decision.requires_mcp)
        self.assertEqual(decision.external_tool_risk, "low")

    def test_create_project_is_medium_risk_controlled_write(self):
        decision = self.policy.classify_task("請建立一個品牌設計專案並製作設計")

        self.assertEqual(decision.intent, "create_project")
        self.assertEqual(decision.risk_level, "medium")
        self.assertTrue(decision.requires_write)
        self.assertFalse(decision.requires_user_approval)

    def test_local_website_request_is_static_site_generation(self):
        decision = self.policy.classify_task("幫我在本地架設一個簡約風網站")

        self.assertEqual(decision.intent, "generate_static_site")
        self.assertEqual(decision.risk_level, "medium")
        self.assertTrue(decision.requires_tools)
        self.assertTrue(decision.requires_write)
        self.assertIn("index.html", " ".join(decision.success_criteria))

    def test_modify_core_file_is_high_risk_patch_only(self):
        decision = self.policy.classify_task("請修改 hermes/core/runtime.py")

        self.assertEqual(decision.intent, "modify_core")
        self.assertEqual(decision.risk_level, "high")
        self.assertTrue(decision.requires_write)
        self.assertTrue(decision.requires_user_approval)

    def test_delete_or_shell_is_rejected(self):
        for task in ["請刪除 hermes 資料夾", "請幫我執行 powershell 指令"]:
            decision = self.policy.classify_task(task)

            self.assertEqual(decision.risk_level, "reject")
            self.assertTrue(decision.requires_user_approval)

    def test_governed_shell_request_requires_approval(self):
        decision = self.policy.classify_task("請從 GitHub clone https://github.com/example/demo 到 user_projects/demo")

        self.assertEqual(decision.intent, "propose_shell_command")
        self.assertEqual(decision.risk_level, "requires_user_approval")
        self.assertTrue(decision.requires_tools)
        self.assertTrue(decision.requires_user_approval)

    def test_git_push_is_classified_as_governed_operation(self):
        for task in ["幫我 git push", "請幫我 git push --force", "推送到 GitHub"]:
            decision = self.policy.classify_task(task)

            self.assertEqual(decision.intent, "propose_shell_command")
            self.assertEqual(decision.risk_level, "requires_user_approval")
            self.assertTrue(decision.requires_tools)
            self.assertTrue(decision.requires_user_approval)

    def test_install_like_requests_are_not_general_chat(self):
        for task in ["pip install requests", "npm install", "下載並安裝 GitHub 套件"]:
            decision = self.policy.classify_task(task)

            self.assertNotEqual(decision.intent, "general_chat")
            self.assertIn(decision.risk_level, {"requires_user_approval", "reject"})


if __name__ == "__main__":
    unittest.main()
