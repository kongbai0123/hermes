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

if __name__ == '__main__':
    unittest.main()
