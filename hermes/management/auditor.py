from pathlib import Path

from hermes.management.decision import AuditResult, ManagedTaskPlan


class ManagementAuditor:
    """Rule-based verifier for managed execution."""

    def __init__(self, tool_registry=None):
        self.tool_registry = tool_registry

    def verify(self, plan: ManagedTaskPlan, step_results: list[tuple]) -> AuditResult:
        if plan.decision.rejected:
            return AuditResult(
                verified=False,
                failed_criteria=["Task rejected by policy"],
                risk_notes=[plan.decision.notes.get("reason", "Rejected by risk gate")],
                final_status="REJECTED",
            )

        result_by_step = {step.id: result for step, result in step_results}
        failed = []
        risk_notes = []

        for step in plan.steps:
            result = result_by_step.get(step.id)
            if result is None:
                failed.append(f"{step.id}: missing TOOL_RESULT")
                continue
            if not result.ok:
                failed.append(f"{step.id}: {result.error or result.summary}")

            if step.tool and step.tool.startswith("mcp."):
                tool_spec = self.tool_registry.get_tool(step.tool) if self.tool_registry else None
                permission = getattr(tool_spec, "permission", None)
                if permission not in {"read", "test"}:
                    failed.append(f"{step.id}: unsafe MCP permission {permission or 'unknown'}")
                else:
                    risk_notes.append(f"{step.id}: MCP tool permission verified as {permission}")

            if step.tool == "propose_shell_command":
                if result.metadata.get("status") != "pending":
                    failed.append(f"{step.id}: shell proposal is not pending approval")
                risk_notes.append(f"{step.id}: shell command gated by approval proposal")
            if step.tool == "execute_approved_shell":
                failed.append(f"{step.id}: direct shell execution is not allowed in managed plan")

            if step.type == "write":
                target = str((result.metadata or {}).get("path", "")).replace("\\", "/")
                if "/user_projects/" not in target:
                    failed.append(f"{step.id}: write outside user_projects")
                else:
                    risk_notes.append(f"{step.id}: write constrained to {Path(target).as_posix()}")

        for criterion in plan.decision.success_criteria:
            if not self._criterion_has_evidence(criterion, step_results):
                failed.append(f"criterion not evidenced: {criterion}")

        return AuditResult(
            verified=not failed,
            failed_criteria=failed,
            risk_notes=risk_notes,
            final_status="DONE" if not failed else "FAILED",
        )

    def _criterion_has_evidence(self, criterion: str, step_results: list[tuple]) -> bool:
        combined = "\n".join(
            [
                f"{step.tool} {result.summary} {result.content} {result.metadata}"
                for step, result in step_results
            ]
        )
        if "user_projects" in criterion:
            return "user_projects" in combined
        if "index.html" in criterion:
            return "index.html" in combined
        if "styles.css" in criterion:
            return "styles.css" in combined
        if "不可改動 Hermes 原始碼" in criterion:
            return True
        if "實際建立的檔案" in criterion:
            return "README.md" in combined or "design_brief.md" in combined
        if "只能列出工具結果證明存在的檔案" in criterion:
            return "index.html" in combined and "styles.css" in combined
        if "測試工具" in criterion:
            return "Tests:" in combined
        if "搜尋結果" in criterion:
            return bool(step_results)
        if "讀取結果" in criterion:
            return bool(step_results)
        if "MCP 工具" in criterion:
            return any(str(step.tool).startswith("mcp.") and result.ok for step, result in step_results)
        if "read-only MCP" in criterion:
            return True
        if "MCP 呼叫" in criterion:
            return any(str(step.tool).startswith("mcp.") and result.ok for step, result in step_results)
        if "直接回答" in criterion:
            return True
        if "shell proposal" in criterion or "approval token" in criterion or "governed shell" in criterion:
            return any(step.tool == "propose_shell_command" and result.ok for step, result in step_results)
        return bool(step_results)
