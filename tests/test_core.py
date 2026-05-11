import unittest
import os
import sys
from pathlib import Path

# 將專案路徑加入 sys.path
sys.path.append(str(Path(__file__).parent.parent))

from hermes.core.state_machine import StateMachine, AgentState
from hermes.core.runtime import HermesRuntime
from hermes.core.llm_provider import MockLLMProvider, OllamaProvider
from hermes.utils.monitor import Monitor
from hermes.harness.constraints import ConstraintValidator

class TestHermesCore(unittest.TestCase):
    def test_state_machine_transition(self):
        sm = StateMachine()
        self.assertEqual(sm.current_state, AgentState.IDLE)
        sm.transition_to(AgentState.PLANNING)
        self.assertEqual(sm.current_state, AgentState.PLANNING)

    def test_monitor_metrics(self):
        m = Monitor()
        m.record_tokens(100, 50)
        self.assertEqual(m.metrics["token_usage"]["total"], 150)

    def test_constraints_safety(self):
        cv = ConstraintValidator()
        # 在 V1 唯讀模式下，所有指令都應該被拒絕
        safe, msg = cv.validate_command("ls -la")
        self.assertFalse(safe)
        self.assertIn("DISABLED", msg)

    def test_runtime_basic_execution(self):
        # 使用 Mock 測試 Runtime 基礎流程
        runtime = HermesRuntime(llm_provider=MockLLMProvider())
        runtime.execute_task("你好")
        status = runtime.get_status()

        self.assertEqual(status["last_result"]["status"], "DONE")
        self.assertTrue(len(status["last_result"]["trace"]) > 0)

    def test_monitor_serializable_traces(self):
        m = Monitor()
        m.add_trace("RUNTIME", "TEST_ACTION", {"key": "value"})
        traces = m.get_serializable_traces()
        self.assertEqual(len(traces), 1)
        self.assertEqual(traces[0]["action"], "TEST_ACTION")

if __name__ == '__main__':
    unittest.main()
