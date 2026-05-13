import unittest
from pathlib import Path

from hermes.harness.constraints import ConstraintValidator
from hermes.harness.executor import SafeExecutor
from hermes.harness.tools import ToolRegistry, ToolSpec
from hermes.core.types import ToolResult
from hermes.management.auditor import ManagementAuditor
from hermes.management.orchestrator import ManagementOrchestrator


class TestManagementOrchestrator(unittest.TestCase):
    def setUp(self):
        self.root = Path("e:/program/hermes/tests/management_workspace").resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        (self.root / "README.md").write_text("Hermes management test", encoding="utf-8")
        (self.root / "user_projects").mkdir(exist_ok=True)
        (self.root / "user_projects" / "agent_skill.md").write_text("User agent skill", encoding="utf-8")
        self.executor = SafeExecutor(ConstraintValidator(workspace_root=str(self.root)))
        self.tools = ToolRegistry(self.executor)
        self.orchestrator = ManagementOrchestrator(self.tools)

    def test_create_project_plan_contains_write_then_verify_steps(self):
        plan = self.orchestrator.plan("請建立一個品牌設計專案並製作設計")

        self.assertEqual(plan.decision.intent, "create_project")
        self.assertEqual([step.tool for step in plan.steps], ["create_project_workspace", "list_files"])
        self.assertEqual(plan.steps[0].type, "write")
        self.assertEqual(plan.steps[1].type, "verify")

    def test_static_site_plan_generates_site_then_verifies_files(self):
        plan = self.orchestrator.plan("幫我在本地架設一個簡約風網站")

        self.assertEqual(plan.decision.intent, "generate_static_site")
        self.assertEqual([step.tool for step in plan.steps], ["generate_static_site", "list_files"])
        self.assertEqual(plan.steps[0].args["name"], "minimal_website")

    def test_read_plan_uses_read_file(self):
        plan = self.orchestrator.plan("請讀取 README.md 並摘要")

        self.assertEqual(plan.decision.intent, "read_workspace")
        self.assertEqual(len(plan.steps), 1)
        self.assertEqual(plan.steps[0].tool, "read_file")
        self.assertEqual(plan.steps[0].args["path"], "README.md")

    def test_read_plan_handles_multiple_files_and_bare_markdown_name(self):
        plan = self.orchestrator.plan("你有看到README.md、agent_skill嗎是否了解")

        self.assertEqual(plan.decision.intent, "read_workspace")
        self.assertEqual([step.tool for step in plan.steps], ["read_file", "read_file"])
        self.assertEqual(plan.steps[0].args["path"], "README.md")
        self.assertEqual(plan.steps[1].args["path"], "user_projects/agent_skill.md")

    def test_execute_plan_stops_on_rejected_task_without_tool_calls(self):
        plan = self.orchestrator.plan("請刪除 hermes 資料夾")
        execution = self.orchestrator.execute(plan)

        self.assertFalse(execution.ok)
        self.assertEqual(execution.audit.final_status, "REJECTED")
        self.assertEqual(execution.step_results, [])

    def test_execute_create_project_and_audit_success(self):
        plan = self.orchestrator.plan("請建立一個品牌設計專案並製作設計")
        execution = self.orchestrator.execute(plan)

        project_dir = self.root / "user_projects" / "generated-project"
        self.assertTrue(execution.ok)
        self.assertTrue(project_dir.is_dir())
        self.assertTrue((project_dir / "README.md").exists())
        self.assertTrue(execution.audit.verified)
        self.assertEqual(execution.audit.final_status, "DONE")

    def test_execute_static_site_creates_real_html_and_css(self):
        plan = self.orchestrator.plan("幫我在本地架設一個簡約風網站")
        execution = self.orchestrator.execute(plan)

        project_dir = self.root / "user_projects" / "minimal_website"
        self.assertTrue(execution.ok)
        self.assertTrue((project_dir / "index.html").exists())
        self.assertTrue((project_dir / "styles.css").exists())
        self.assertTrue(execution.audit.verified)

    def test_auditor_detects_missing_required_step_result(self):
        plan = self.orchestrator.plan("請建立一個品牌設計專案並製作設計")
        audit = ManagementAuditor().verify(plan, [])

        self.assertFalse(audit.verified)
        self.assertIn("S1", ",".join(audit.failed_criteria))

    def test_mcp_read_plan_uses_registered_read_only_mcp_tool(self):
        self.tools.add_tool(ToolSpec(
            name="mcp.echo.read_note",
            description="Read note through MCP",
            permission="read",
            handler=lambda **kwargs: ToolResult(ok=True, tool="mcp.echo.read_note", summary="ok", content="note"),
        ))
        orchestrator = ManagementOrchestrator(self.tools)

        plan = orchestrator.plan("請用 MCP 讀取 note")

        self.assertEqual(plan.decision.intent, "mcp_read")
        self.assertTrue(plan.decision.requires_mcp)
        self.assertEqual(plan.steps[0].tool, "mcp.echo.read_note")
        self.assertEqual(plan.steps[0].type, "read")

    def test_auditor_rejects_mcp_tool_with_unsafe_permission(self):
        self.tools.add_tool(ToolSpec(
            name="mcp.echo.create_note",
            description="Unsafe MCP write",
            permission="write",
            handler=lambda **kwargs: ToolResult(ok=True, tool="mcp.echo.create_note", summary="ok"),
        ))
        plan = self.orchestrator.plan("請用 MCP 讀取 note")
        plan.steps[0].tool = "mcp.echo.create_note"

        audit = ManagementAuditor(tool_registry=self.tools).verify(
            plan,
            [(plan.steps[0], ToolResult(ok=True, tool="mcp.echo.create_note", summary="ok"))],
        )

        self.assertFalse(audit.verified)
        self.assertIn("unsafe MCP permission", " ".join(audit.failed_criteria))

    def test_shell_task_generates_proposal_step_not_direct_execution(self):
        plan = self.orchestrator.plan("請從 GitHub clone https://github.com/example/demo 到 user_projects/demo")

        self.assertEqual(plan.decision.intent, "propose_shell_command")
        self.assertEqual(plan.steps[0].tool, "propose_shell_command")
        self.assertEqual(plan.steps[0].type, "generate")
        self.assertNotEqual(plan.steps[0].tool, "execute_approved_shell")


if __name__ == "__main__":
    unittest.main()
