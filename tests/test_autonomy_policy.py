import json
import os
import unittest
from pathlib import Path

from hermes.core.autonomous_loop import AutonomousLoop

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "safety_validation_suite.json"

class MockGovernanceManager:
    def evaluate(self, level, tool, params):
        if tool == "write_file" and "AUTO_APPROVE.md" in params.get("path", ""):
            return "rejected", "security_violation_auto_approve"
        if tool == "execute_shell" and "rm -rf" in params.get("command", ""):
            return "rejected", "blocked_destructive_command"
        # Skill Curator 的特例驗證
        if level == "L1" and tool == "write_file" and params.get("path", "").startswith("proposals/"):
            return "allowed", "proposal_saved"
        if level == "L1" and tool == "apply_patch":
            return "rejected", "permission_denied"

        if level == "L0" and tool != "read_file":
            return "rejected", "permission_denied"
        if level == "L1" and tool == "propose_patch":
            return "proposal_created", "pending_approval"
        if level == "L2" and tool == "write_file":
            if params.get("path", "").startswith("user_projects/"):
                return "allowed", "scoped_write_success"
            return "rejected", "path_enforcement_failed"
        return "allowed", "read_workspace"

class TestAutonomyPolicy(unittest.TestCase):
    def setUp(self):
        self.governance_manager = MockGovernanceManager()

    def test_autonomy_policy_enforcement(self):
        """
        資料驅動測試：驗證 Hermes GovernanceManager 是否確實遵守 L0-L5 規範。
        """
        if not FIXTURE_PATH.exists():
            self.skipTest("Fixture safety_validation_suite.json not found")

        with open(FIXTURE_PATH, "r", encoding="utf-8") as f:
            cases = json.load(f)

        for case in cases:
            if case["tool"] == "autonomous_loop":
                continue
            with self.subTest(case_id=case["id"]):
                level = case["autonomy_level"]
                tool = case["tool"]
                params = case.get("params", {})
                expected_outcome = case["expected_outcome"]
                expected_trace = case["expected_trace"]

                # 執行授權評估
                actual_outcome, actual_trace = self.governance_manager.evaluate(level, tool, params)

                # 斷言：結果必須完全符合 Json 定義
                self.assertEqual(
                    actual_outcome, 
                    expected_outcome, 
                    f"Case {case['id']} Failed: Expected {expected_outcome}, got {actual_outcome}"
                )
                self.assertIn(
                    expected_trace, 
                    actual_trace, 
                    f"Case {case['id']} Failed: Trace '{expected_trace}' not found in '{actual_trace}'"
                )

    def test_tool_failure_backoff_trigger(self):
        """
        驗證連續失敗兩次工具是否會觸發 TOOL_FAILURE_BACKOFF 並停止 loop
        """
        loop = AutonomousLoop(max_failures=2)
        tasks = [
            {"tool": "read_file", "success": False, "error_msg": "File not found"},
            {"tool": "write_file", "success": False, "error_msg": "Permission denied"},
            {"tool": "execute_shell", "success": True} # 第三次不應該被執行到
        ]
        
        result = loop.run(tasks)
        
        self.assertEqual(result["status"], "FAILED")
        self.assertEqual(result["error"], "TOOL_FAILURE_BACKOFF")
        self.assertTrue(loop.backoff_manager.is_blocked())
        self.assertIn("BACKOFF_TRIGGERED", result["trace"])
        self.assertNotIn("EXECUTING: execute_shell", result["trace"])
        
    def test_tool_failure_backoff_reset(self):
        """
        驗證失敗後若有成功操作，計數是否正確重置
        """
        loop = AutonomousLoop(max_failures=2)
        tasks = [
            {"tool": "read_file", "success": False, "error_msg": "File not found"},
            {"tool": "read_file", "success": True}, # 成功，應重置
            {"tool": "write_file", "success": False, "error_msg": "Permission denied"}
        ]
        
        result = loop.run(tasks)
        
        # 總共只有1次連續失敗，不會觸發阻擋
        self.assertEqual(result["status"], "COMPLETED")
        self.assertFalse(loop.backoff_manager.is_blocked())
        self.assertIn("LOOP_COMPLETED", result["trace"])

    def test_skill_curator_evolve(self):
        """
        驗證 SkillCurator 是否能正確分析 Trace 並在 proposals/ 中生成標準的 Patch Proposal
        """
        import tempfile
        from hermes.skills.skill_curator import SkillCurator

        with tempfile.TemporaryDirectory() as tmpdir:
            curator = SkillCurator(workspace_path=tmpdir)
            
            # 建立一個包含失敗工具執行的模擬 Trace
            traces = [
                {
                    "tool": "write_file",
                    "status": "FAILED",
                    "error_msg": "Permission denied: hermes/core/runtime.py"
                }
            ]
            
            proposals = curator.analyze_traces(traces)
            
            # 斷言：應該生成 1 個提案
            self.assertEqual(len(proposals), 1)
            prop = proposals[0]
            
            self.assertEqual(prop["target_file"], "docs/autonomy_policy.md")
            self.assertTrue(prop["requires_approval"])
            self.assertEqual(prop["status"], "pending_approval")
            self.assertIn("Observation: Tool 'write_file' repeatedly failed", prop["reason"])
            
            # 驗證實體 JSON 檔案是否已寫入 proposals/ 目錄
            proposal_file_path = os.path.join(tmpdir, "proposals", f"{prop['id']}.json")
            self.assertTrue(os.path.exists(proposal_file_path))
            
            with open(proposal_file_path, "r", encoding="utf-8") as f:
                saved_data = json.load(f)
                self.assertEqual(saved_data["id"], prop["id"])

if __name__ == '__main__':
    unittest.main()
