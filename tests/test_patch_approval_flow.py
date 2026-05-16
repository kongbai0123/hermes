import unittest
import json
from hermes.core.runtime import HermesRuntime
from hermes.core.llm_provider import MockLLMProvider
from hermes.harness.patch import PatchProposal, FileChange
from hermes.harness.executor import ToolResult

class TestPatchApprovalFlow(unittest.TestCase):
    def setUp(self):
        self.runtime = HermesRuntime(llm_provider=MockLLMProvider())
        # Ensure we have a clean state
        self.runtime.governance.revoke_permission("filesystem_write")

    def test_full_approval_flow(self):
        # 1. Propose a patch
        proposal = PatchProposal(
            task_id="test_task",
            changes=[
                FileChange(path="test_file.txt", operation="create", replacement="Hello World", reason="test")
            ]
        )
        self.runtime.executor.approval_manager.register_proposal(proposal)
        patch_id = proposal.id
        
        # 2. Check initial state (should fail without permission)
        # We need a token first
        token = self.runtime.executor.approval_manager.approve(patch_id)
        self.assertIsNotNone(token)
        
        # 3. Attempt apply (should fail if governance is not authorized)
        # Note: In start_hermes.py, approve() automatically grants permission. 
        # Here we test the underlying executor logic.
        result = self.runtime.executor.apply_approved_patch(patch_id, token)
        self.assertFalse(result.ok)
        self.assertEqual(result.summary, "Governance Blocked")
        
        # 4. Grant permission and try again
        self.runtime.governance.grant_permission("filesystem_write")
        result = self.runtime.executor.apply_approved_patch(patch_id, token)
        
        # 5. Verify success
        self.assertTrue(result.ok)
        self.assertIn("successfully", result.summary)
        
        # Cleanup
        import os
        if os.path.exists("test_file.txt"):
            os.remove("test_file.txt")

    def test_invalid_token(self):
        proposal = PatchProposal(task_id="t1", changes=[FileChange(path="x.txt", operation="create", replacement="y", reason="z")])
        self.runtime.executor.approval_manager.register_proposal(proposal)
        
        self.runtime.governance.grant_permission("filesystem_write")
        result = self.runtime.executor.apply_approved_patch(proposal.id, "invalid_token")
        self.assertFalse(result.ok)
        self.assertEqual(result.summary, "Unauthorized")

if __name__ == "__main__":
    unittest.main()
