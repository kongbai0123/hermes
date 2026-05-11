import unittest
import os
import sys

# 將專案路徑加入 sys.path 以利測試
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from hermes.core.state_machine import StateMachine, AgentState
from hermes.core.runtime import HermesRuntime
from hermes.core.llm_provider import MockLLMProvider, OllamaProvider, create_llm_provider
from hermes.utils.monitor import Monitor
from hermes.harness.constraints import ConstraintValidator

class TestHermesCore(unittest.TestCase):
    def test_state_machine_transition(self):
        sm = StateMachine()
        self.assertEqual(sm.current_state, AgentState.IDLE)
        sm.transition_to(AgentState.PLANNING)
        self.assertEqual(sm.current_state, AgentState.PLANNING)
        self.assertEqual(len(sm.get_history()), 1)

    def test_monitor_metrics(self):
        m = Monitor()
        m.record_tokens(100, 50)
        self.assertEqual(m.metrics["token_usage"]["total"], 150)
        m.record_latency("test", 0.5)
        self.assertEqual(len(m.metrics["latency"]), 1)

    def test_monitor_reset_clears_runtime_counters(self):
        m = Monitor()
        m.record_tokens(100, 50)
        m.record_latency("test", 0.5)
        m.record_error("TEST", "boom")
        m.add_trace("DONE", "USER_RESPONSE", {"response": "ok"})

        m.reset()

        self.assertEqual(m.metrics["token_usage"]["total"], 0)
        self.assertEqual(m.metrics["latency"], [])
        self.assertEqual(m.metrics["errors"], [])
        self.assertEqual(m.traces, [])

    def test_constraints_safety(self):
        cv = ConstraintValidator()
        safe, msg = cv.validate_command("ls -la")
        self.assertTrue(safe)
        
        unsafe, msg = cv.validate_command("rm -rf /")
        self.assertFalse(unsafe)

    def test_runtime_returns_user_visible_reply(self):
        runtime = HermesRuntime(llm_provider=MockLLMProvider())
        runtime.memory.consolidate_session = lambda task, result: None

        result = runtime.execute_task("你好")
        status = runtime.get_status()

        self.assertEqual(result["status"], "DONE")
        self.assertEqual(result["task"], "你好")
        self.assertIn("response", result)
        self.assertTrue(result["response"])
        self.assertEqual(status["last_result"], result)
        self.assertTrue(
            any(trace["action"] == "USER_RESPONSE" for trace in runtime.monitor.traces)
        )

    def test_provider_factory_creates_ollama_with_options(self):
        provider = create_llm_provider("llama3", temperature=0.2)

        self.assertIsInstance(provider, OllamaProvider)
        self.assertEqual(provider.model, "llama3")
        self.assertEqual(provider.temperature, 0.2)

    def test_provider_factory_keeps_mock_available(self):
        provider = create_llm_provider("mock")

        self.assertIsInstance(provider, MockLLMProvider)

    def test_runtime_reconfigures_llm_and_verifier_together(self):
        runtime = HermesRuntime(llm_provider=MockLLMProvider())
        provider = create_llm_provider("llama3", temperature=0.4)

        runtime.configure_llm(provider)

        self.assertIs(runtime.llm, provider)
        self.assertIs(runtime.verifier.llm, provider)

    def test_runtime_reports_provider_errors_to_user(self):
        class BrokenProvider(MockLLMProvider):
            def completion(self, prompt, system_prompt=None):
                raise Exception("provider offline")

        runtime = HermesRuntime(llm_provider=BrokenProvider())
        result = runtime.execute_task("你好")

        self.assertEqual(result["status"], "FAILED")
        self.assertEqual(result["error"], "provider offline")
        self.assertEqual(runtime.get_status()["last_result"], result)

if __name__ == '__main__':
    unittest.main()
