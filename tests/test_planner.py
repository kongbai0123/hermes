import unittest
from hermes.core.tool_planner import ToolPlanner
from hermes.harness.tools import ToolRegistry
from hermes.harness.executor import SafeExecutor
from hermes.harness.constraints import ConstraintValidator

class TestToolPlanner(unittest.TestCase):
    def setUp(self):
        self.constraints = ConstraintValidator()
        self.executor = SafeExecutor(self.constraints)
        self.registry = ToolRegistry(self.executor)
        self.planner = ToolPlanner(self.registry)

    def test_parse_standard_json(self):
        # 測試標準 JSON
        output = '{"tool": "read_file", "args": {"path": "test.py"}, "reason": "test"}'
        plan = self.planner.parse_output(output)
        self.assertIsNotNone(plan)
        self.assertEqual(plan.tool, "read_file")
        self.assertEqual(plan.args["path"], "test.py")

    def test_parse_json_in_markdown(self):
        # 測試 Markdown 包裹
        output = 'Here is the plan:\n```json\n{"tool": "list_files", "args": {"path": "."}}\n```'
        plan = self.planner.parse_output(output)
        self.assertIsNotNone(plan)
        self.assertEqual(plan.tool, "list_files")
        self.assertEqual(plan.args["path"], ".")

    def test_heuristic_fallback_read(self):
        # 測試啟發式偵測
        output = '我現在去讀取 start_hermes.py 來看看。'
        plan = self.planner.parse_output(output)
        self.assertIsNotNone(plan)
        self.assertEqual(plan.tool, "read_file")
        self.assertEqual(plan.args["path"], "start_hermes.py")

    def test_heuristic_fallback_list(self):
        output = '好的，我先列出目前的目錄清單。'
        plan = self.planner.parse_output(output)
        self.assertIsNotNone(plan)
        self.assertEqual(plan.tool, "list_files")
        self.assertEqual(plan.args["path"], ".")

    def test_parse_design_generation_json_preserves_goal(self):
        output = '{"tool": "generate_design_artifact", "args": {"goal": "幫我設計一個咖啡店網站"}}'
        plan = self.planner.parse_output(output)
        self.assertIsNotNone(plan)
        self.assertEqual(plan.tool, "generate_design_artifact")
        self.assertEqual(plan.args["goal"], "幫我設計一個咖啡店網站")

    def test_heuristic_fallback_design_generation(self):
        output = '幫我製作一個簡潔的網站設計方案'
        plan = self.planner.parse_output(output)
        self.assertIsNotNone(plan)
        self.assertEqual(plan.tool, "generate_design_artifact")
        self.assertIn("網站設計方案", plan.args["goal"])

    def test_plain_test_word_does_not_trigger_run_tests(self):
        output = '你好，這是 UI 模型切換測試。'
        plan = self.planner.parse_output(output)
        self.assertIsNone(plan)

    def test_explicit_run_test_intent_triggers_run_tests(self):
        output = '請幫我執行測試'
        plan = self.planner.parse_output(output)
        self.assertIsNotNone(plan)
        self.assertEqual(plan.tool, "run_tests")

    def test_heuristic_create_workspace_intent_triggers_project_tool(self):
        output = '請在不動到 hermes 原始碼的前提下，建立一個資料夾並製作網頁設計'
        plan = self.planner.parse_output(output)

        self.assertIsNotNone(plan)
        self.assertEqual(plan.tool, "create_project_workspace")
        self.assertEqual(plan.args["name"], "generated-project")
        self.assertIn("網頁設計", plan.args["brief"])

if __name__ == '__main__':
    unittest.main()
