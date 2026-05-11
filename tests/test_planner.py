import unittest
from hermes.core.tool_planner import ToolPlanner
from hermes.harness.tools import ToolRegistry
from hermes.harness.executor import SafeExecutor
from hermes.harness.constraints import ConstraintValidator

class TestToolPlanner(unittest.TestCase):
    def setUp(self):
        # 初始化環境
        self.constraints = ConstraintValidator()
        self.executor = SafeExecutor(self.constraints)
        self.registry = ToolRegistry(self.executor)
        self.planner = ToolPlanner(self.registry)

    def test_parse_standard_json(self):
        output = '{"tool": "read_file", "args": {"file_path": "test.py"}, "reason": "test"}'
        plan = self.planner.parse_output(output)
        self.assertIsNotNone(plan)
        self.assertEqual(plan.tool, "read_file")
        self.assertEqual(plan.args["file_path"], "test.py")

    def test_parse_json_in_markdown(self):
        output = 'Here is the plan:\n```json\n{"tool": "list_files", "args": {"directory": "."}}\n```'
        plan = self.planner.parse_output(output)
        self.assertIsNotNone(plan)
        self.assertEqual(plan.tool, "list_files")

    def test_heuristic_fallback_read(self):
        # 測試模型沒給 JSON 但明確說了讀取某個檔案
        output = '我現在去讀取 start_hermes.py 來看看。'
        plan = self.planner.parse_output(output)
        self.assertIsNotNone(plan)
        self.assertEqual(plan.tool, "read_file")
        self.assertEqual(plan.args["file_path"], "start_hermes.py")

    def test_heuristic_fallback_list(self):
        output = '好的，我先列出目前的目錄清單。'
        plan = self.planner.parse_output(output)
        self.assertIsNotNone(plan)
        self.assertEqual(plan.tool, "list_files")
        self.assertEqual(plan.args["directory"], ".")

    def test_invalid_tool(self):
        output = '{"tool": "delete_all_files", "args": {}}'
        plan = self.planner.parse_output(output)
        self.assertIsNone(plan) # 應該因為工具未註冊而回傳 None

if __name__ == '__main__':
    unittest.main()
