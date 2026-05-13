import sys
import unittest
import asyncio
from pathlib import Path

from hermes.harness.constraints import ConstraintValidator
from hermes.harness.executor import SafeExecutor

try:
    from hermes.api import server
except ModuleNotFoundError:
    server = None


class TestGovernedShell(unittest.TestCase):
    def setUp(self):
        self.root = Path("e:/program/hermes/tests/shell_workspace").resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        (self.root / "user_projects").mkdir(exist_ok=True)
        self.executor = SafeExecutor(ConstraintValidator(workspace_root=str(self.root)))

    def test_propose_shell_command_creates_pending_action_without_execution(self):
        result = self.executor.propose_shell_command(
            command=f"{sys.executable} --version",
            reason="確認 Python 可用",
            cwd=".",
        )

        self.assertTrue(result.ok)
        self.assertEqual(result.tool, "propose_shell_command")
        self.assertIn("pending approval", result.summary.lower())
        proposal_id = result.metadata["proposal_id"]
        self.assertIn(proposal_id, self.executor.shell_approval_manager.pending_actions)

    def test_unsafe_shell_command_is_rejected_before_proposal(self):
        result = self.executor.propose_shell_command(
            command="del important.txt",
            reason="unsafe",
            cwd=".",
        )

        self.assertFalse(result.ok)
        self.assertIn("blocked", result.summary.lower())

    def test_execute_shell_requires_valid_approval_token(self):
        proposal = self.executor.propose_shell_command(
            command=f"{sys.executable} --version",
            reason="確認 Python 可用",
            cwd=".",
        )

        result = self.executor.execute_approved_shell(
            proposal_id=proposal.metadata["proposal_id"],
            approval_token="bad-token",
        )

        self.assertFalse(result.ok)
        self.assertIn("Unauthorized", result.summary)

    def test_execute_approved_shell_runs_whitelisted_command(self):
        proposal = self.executor.propose_shell_command(
            command=f"{sys.executable} --version",
            reason="確認 Python 可用",
            cwd=".",
        )
        token = self.executor.shell_approval_manager.approve(proposal.metadata["proposal_id"])

        result = self.executor.execute_approved_shell(
            proposal_id=proposal.metadata["proposal_id"],
            approval_token=token,
        )

        self.assertTrue(result.ok)
        self.assertEqual(result.tool, "execute_approved_shell")
        self.assertIn("Python", result.content)
        self.assertEqual(result.metadata["returncode"], 0)

    def test_api_lists_approves_and_executes_shell_proposal(self):
        if server is None:
            self.skipTest("FastAPI is not installed in this test environment")
        previous_runtime = server.runtime
        server.runtime = type("RuntimeStub", (), {})()
        server.runtime.executor = self.executor
        try:
            proposal = self.executor.propose_shell_command(
                command=f"{sys.executable} --version",
                reason="確認 Python 可用",
                cwd=".",
            )
            proposal_id = proposal.metadata["proposal_id"]

            pending = asyncio.run(server.get_pending_shell_actions())
            approval = asyncio.run(server.approve_shell_action(proposal_id))
            execution = asyncio.run(server.execute_shell_action(proposal_id=proposal_id, token=approval["token"]))
        finally:
            server.runtime = previous_runtime

        self.assertEqual(pending[0]["id"], proposal_id)
        self.assertEqual(approval["proposal_id"], proposal_id)
        self.assertEqual(execution["details"]["metadata"]["returncode"], 0)


if __name__ == "__main__":
    unittest.main()
