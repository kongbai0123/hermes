import unittest
from hermes.core.runtime import HermesRuntime
from hermes.core.llm_provider import MockLLMProvider

class TestRuntimeRejectionDetails(unittest.TestCase):
    def setUp(self):
        self.runtime = HermesRuntime(llm_provider=MockLLMProvider())

    def test_destructive_request_has_descriptive_rejection(self):
        """輸入：'請刪除 tests 資料夾'，預期 status == 'FAILED' 且 error 包含關鍵資訊"""
        task = "請刪除 tests 資料夾"
        result = self.runtime.execute_task(task)
        
        self.assertEqual(result["status"], "FAILED")
        error_msg = result["error"]
        
        # 預期格式: Rejected by ManagementPolicy: {intent} ({risk_level}) - {reason}
        self.assertIn("Rejected by ManagementPolicy", error_msg)
        self.assertIn("rejected_destructive_request", error_msg)
        self.assertIn("(reject)", error_msg)
        
        # Reason 應包含 destructive 或 刪除 相關字眼 (根據 policy.py)
        # 在 policy.py 中，rejected_destructive_request 的 reason 通常是 "destructive operation is disabled"
        self.assertTrue("destructive" in error_msg.lower() or "刪除" in error_msg)

    def test_shell_request_has_descriptive_rejection(self):
        """輸入：'請執行 powershell 指令'，預期 status == 'FAILED' 且 error 包含 shell 關鍵字"""
        task = "請執行 powershell 指令"
        result = self.runtime.execute_task(task)
        
        self.assertEqual(result["status"], "FAILED")
        error_msg = result["error"]
        
        self.assertIn("Rejected by ManagementPolicy", error_msg)
        self.assertIn("rejected_shell_request", error_msg)
        self.assertIn("(reject)", error_msg)

    def test_rejection_trace_preserves_decision(self):
        """預期 trace 中存在 EXECUTIVE_DECISION，且 data.intent 正確"""
        task = "請刪除 tests 資料夾"
        self.runtime.execute_task(task)
        
        traces = self.runtime.monitor.traces
        executive_decisions = [t for t in traces if getattr(t, 'event_type', None) == "EXECUTIVE_DECISION"]
        
        self.assertTrue(len(executive_decisions) > 0)
        decision_data = executive_decisions[0].payload
        self.assertEqual(decision_data["intent"], "rejected_destructive_request")
        self.assertEqual(decision_data["risk_level"], "reject")
        self.assertTrue("notes" in decision_data)

if __name__ == "__main__":
    unittest.main()
