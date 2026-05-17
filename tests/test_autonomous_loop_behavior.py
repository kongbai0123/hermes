import unittest
import sys
import os
from pathlib import Path

# 將專案路徑加入 sys.path
sys.path.append(str(Path(__file__).parent.parent))

from hermes.core.runtime import HermesRuntime
from hermes.core.llm_provider import LLMProvider
from hermes.core.types import ToolResult

class ScriptedLoopProvider(LLMProvider):
    def __init__(self, responses):
        self.responses = responses
        self.idx = 0
        self.calls = []

    def completion(self, prompt, system_prompt=None):
        self.calls.append({"prompt": prompt, "system_prompt": system_prompt})
        if self.idx < len(self.responses):
            resp = self.responses[self.idx]
            self.idx += 1
            if isinstance(resp, dict) and "tool" in resp:
                import json
                return {"text": json.dumps(resp)}
            elif isinstance(resp, dict) and "final" in resp:
                return {"text": resp["final"]}
            return {"text": str(resp)}
        return {"text": "No more responses planned."}

class TestAutonomousLoopBehavior(unittest.TestCase):
    def test_autonomous_loop_can_chain_multiple_read_tools(self):
        # 驗證 Hermes 是否會做 list_files -> read_file -> final answer
        responses = [
            {"thought": "Checking directory", "tool": "list_files", "args": {"path": "."}},
            {"thought": "Reading README", "tool": "read_file", "args": {"path": "README.md"}},
            {"final": "README contains Hermes info."}
        ]
        runtime = HermesRuntime(llm_provider=ScriptedLoopProvider(responses))
        
        result = runtime.execute_task("Analyze project")
        
        self.assertEqual(result["status"], "DONE")
        self.assertIn("README contains Hermes info", result["response"])
        
        # 檢查 Trace 是否包含對應的工具呼叫
        tool_calls = [t for t in result["trace"] if t["action"] == "TOOL_CALL"]
        self.assertEqual(len(tool_calls), 2)
        self.assertEqual(tool_calls[0]["data"]["tool"], "list_files")
        self.assertEqual(tool_calls[1]["data"]["tool"], "read_file")

    def test_autonomous_loop_blocks_write_and_shell_even_if_llm_requests_it(self):
        # 驗證 Loop 是否會阻斷不安全工具
        responses = [
            {"thought": "Trying to write directly", "tool": "generate_static_site", "args": {"name": "hack", "brief": "unsafe"}}
        ]
        runtime = HermesRuntime(llm_provider=ScriptedLoopProvider(responses))
        
        result = runtime.execute_task("Analyze project")
        
        # 應該被阻斷，狀態改為 FAILED
        self.assertEqual(result["status"], "FAILED")
        self.assertIn("Blocked high-risk tool", result["error"])
        
        # Trace 中應該只有 TOOL_PLAN，沒有 TOOL_CALL
        actions = [t["action"] for t in result["trace"]]
        self.assertIn("TOOL_PLAN", actions)
        self.assertNotIn("TOOL_CALL", actions)

    def test_autonomous_loop_stops_after_max_iterations(self):
        # 驗證是否會截斷無限循環
        class AlwaysListProvider(LLMProvider):
            def completion(self, prompt, system_prompt=None):
                import json
                return {"text": json.dumps({"tool": "list_files", "args": {"path": "."}})}
                
        runtime = HermesRuntime(llm_provider=AlwaysListProvider())
        
        # 設定較小的迭代次數方便測試
        result = runtime.execute_task("Infinite loop", max_iterations=3)
        
        # 雖然 LLM 一直想要 list_files，但 runtime 應該在 3 次後停止並摘要
        self.assertEqual(result["status"], "DONE")
        
        tool_calls = [t for t in result["trace"] if t["action"] == "TOOL_CALL"]
        self.assertEqual(len(tool_calls), 3)

    def test_autonomous_loop_failure_backoff(self):
        # 驗證如果工具連續失敗，是否會觸發 TOOL_BACKOFF trace 與時間延遲
        responses = [
            {"thought": "Reading non-existent file", "tool": "read_file", "args": {"path": "non_existent_file_123.txt"}},
            {"thought": "Reading again", "tool": "read_file", "args": {"path": "non_existent_file_123.txt"}},
            {"final": "Done trying."}
        ]
        runtime = HermesRuntime(llm_provider=ScriptedLoopProvider(responses))
        
        import unittest.mock as mock
        with mock.patch("time.sleep") as mock_sleep:
            result = runtime.execute_task("Read non-existent file twice")
            
            # 應順利完成任務，狀態為 DONE
            self.assertEqual(result["status"], "DONE")
            
            # 驗證是否寫入 TOOL_BACKOFF 類型的 trace
            backoff_traces = [t for t in result["trace"] if t["action"] == "TOOL_BACKOFF"]
            self.assertEqual(len(backoff_traces), 1)
            self.assertEqual(backoff_traces[0]["data"]["tool"], "read_file")
            self.assertEqual(backoff_traces[0]["data"]["consecutive_failures"], 2)
            self.assertEqual(backoff_traces[0]["data"]["backoff_duration_seconds"], 2)
            
            # 驗證 time.sleep 被調用了 2 秒
            mock_sleep.assert_called_once_with(2)

if __name__ == '__main__':
    unittest.main()

