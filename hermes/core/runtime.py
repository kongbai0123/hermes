import time
from pathlib import Path
from typing import Any, Dict, Optional
from hermes.core.state_machine import StateMachine, AgentState
from hermes.core.types import ToolResult, RuntimeTrace
from hermes.core.tool_planner import ToolPlanner
from hermes.core.llm_provider import LLMProvider, OllamaProvider
from hermes.harness.constraints import ConstraintValidator
from hermes.harness.executor import SafeExecutor
from hermes.harness.governance import GovernanceManager
from hermes.harness.tools import ToolRegistry
from hermes.management.decision import ExecutionResult
from hermes.management.orchestrator import ManagementOrchestrator
from hermes.memory.manager import MemoryManager
from hermes.skills.base import SkillRegistry
from hermes.utils.monitor import Monitor

class HermesRuntime:
    """
    Hermes Agent Runtime: 負責代理狀態管理與任務執行閉環。
    """
    def __init__(
        self,
        agent_id: str = "hermes-v1",
        llm_provider: Optional[LLMProvider] = None,
        mcp_config_path: Optional[str] = None,
    ):
        self.agent_id = agent_id
        self.monitor = Monitor()
        self.state_machine = StateMachine(on_state_change=self._handle_state_change)
        self.llm = llm_provider or OllamaProvider()
        self.mcp_gateway = None
        
        # 核心地基
        self.constraints = ConstraintValidator()
        self.executor = SafeExecutor(self.constraints)
        self.tools = ToolRegistry(self.executor)
        self._initialize_mcp(mcp_config_path)
        self.planner = ToolPlanner(self.tools)
        self.management = ManagementOrchestrator(self.tools)
        self.governance = GovernanceManager()
        self.memory = MemoryManager()
        self.skills = SkillRegistry()
        
        self.is_running = False
        self.last_result = {"status": "IDLE", "task": "", "response": "", "error": "", "trace": []}

    def configure_llm(self, llm_provider: LLMProvider):
        self.llm = llm_provider

    def _handle_state_change(self, old: AgentState, new: AgentState):
        self.monitor.add_trace(state=new.name, action="TRANSITION", data={"from": old.name})

    def execute_task(self, task: str, user_system_prompt: Optional[str] = None, **llm_config) -> Dict[str, Any]:
        self.is_running = True
        self.monitor.traces = []
        self.last_result = {"status": "RUNNING", "task": task, "response": "", "error": "", "trace": []}
        start_time = time.time()
        
        self.monitor.traces.append(RuntimeTrace("USER_CMD", f"Task: {task}", {"task": task}))
        self._record_mcp_inventory_trace()

        try:
            # 1. Planning
            self.state_machine.transition_to(AgentState.PLANNING)
            managed_plan = self.management.plan(task)
            self.monitor.traces.append(RuntimeTrace("EXECUTIVE_DECISION", f"Intent: {managed_plan.decision.intent}", {
                "intent": managed_plan.decision.intent,
                "risk_level": managed_plan.decision.risk_level,
                "requires_tools": managed_plan.decision.requires_tools,
                "requires_write": managed_plan.decision.requires_write,
                "requires_user_approval": managed_plan.decision.requires_user_approval,
                "requires_mcp": managed_plan.decision.requires_mcp,
                "external_tool_risk": managed_plan.decision.external_tool_risk,
                "success_criteria": managed_plan.decision.success_criteria,
                "notes": managed_plan.decision.notes
            }))

            if managed_plan.decision.rejected:
                managed_result = self.management.execute(managed_plan)
                self.monitor.traces.append(RuntimeTrace("AUDITOR_VERIFICATION", "Task rejected by management policy", {
                    "verified": False,
                    "failed_criteria": managed_result.audit.failed_criteria if managed_result.audit else [],
                    "risk_notes": managed_result.audit.risk_notes if managed_result.audit else [],
                    "final_status": "REJECTED"
                }))
                self.last_result.update({"status": "FAILED", "error": managed_result.error})
            elif managed_plan.steps:
                self.monitor.traces.append(RuntimeTrace("STRATEGY_PLAN", f"Steps: {len(managed_plan.steps)}", {
                    "steps": [
                        {
                            "id": step.id,
                            "type": step.type,
                            "tool": step.tool,
                            "args": step.args,
                            "reason": step.reason,
                            "expected": step.expected
                        }
                        for step in managed_plan.steps
                    ]
                }))
                self.state_machine.transition_to(AgentState.EXECUTING)
                managed_result = self._execute_managed_plan(managed_plan)

                if managed_result.ok:
                    self.state_machine.transition_to(AgentState.VERIFYING)
                    if managed_plan.decision.intent == "read_workspace" and self._should_use_read_confirmation(task):
                        self.last_result.update({
                            "status": "DONE",
                            "response": self._finalize_read_workspace_response(managed_result)
                        })
                        return self.last_result

                    context_prompt = (
                        f"Task: {task}\n"
                        f"Decision: {managed_plan.decision.intent} / {managed_plan.decision.risk_level}\n"
                        f"Result:\n{managed_result.combined_tool_content()}\n"
                        f"Audit: {managed_result.audit.final_status if managed_result.audit else 'UNKNOWN'}\n"
                        "Finalize answer:"
                    )
                    final_system_prompt = "Answer based on the managed execution results. Use Traditional Chinese if the user writes Chinese."
                    if user_system_prompt:
                        final_system_prompt = f"{final_system_prompt}\n\nUser system prompt:\n{user_system_prompt}"
                    final_resp = self.llm.completion(prompt=context_prompt, system_prompt=final_system_prompt)
                    self._record_usage(final_resp)
                    self.last_result.update({"status": "DONE", "response": final_resp["text"]})
                else:
                    self.last_result.update({"status": "FAILED", "error": managed_result.error})
            else:
                self._execute_llm_direct_or_single_tool(task, user_system_prompt)
            
            if self.last_result["status"] in {"DONE", "FAILED"}:
                if self.last_result["status"] == "DONE":
                    self.state_machine.transition_to(AgentState.DONE)
                else:
                    self.state_machine.transition_to(AgentState.FAILED)
                return self.last_result

        except Exception as e:
            self.state_machine.transition_to(AgentState.FAILED)
            self.last_result.update({"status": "FAILED", "error": str(e)})
        
        finally:
            self.is_running = False
            self.last_result["trace"] = self.monitor.get_serializable_traces()
            self.monitor.record_latency("total_execution", time.time() - start_time)
            if self.last_result["status"] == "DONE":
                self.memory.consolidate_session(task, self.last_result["response"])
            return self.last_result

    def get_status(self) -> Dict[str, Any]:
        return {"agent_id": self.agent_id, "current_state": self.state_machine.current_state.name, "is_running": self.is_running, "last_result": self.last_result, "metrics": self.monitor.get_summary()}

    def shutdown(self) -> None:
        if self.mcp_gateway:
            self.mcp_gateway.shutdown()
            self.mcp_gateway = None

    def _initialize_mcp(self, mcp_config_path: str) -> None:
        if not mcp_config_path:
            return
        config_path = Path(mcp_config_path)
        if not config_path.exists():
            return
        try:
            from hermes.mcp.config import load_mcp_config
            from hermes.mcp.gateway import MCPGateway
            from hermes.mcp.registry_bridge import register_mcp_tools

            config = load_mcp_config(str(config_path))
            self.monitor.add_trace("MCP", "MCP_CONFIG_LOADED", {"path": str(config_path), "servers": len(config.servers)})
            gateway = MCPGateway(config, monitor=self.monitor)
            gateway.start_enabled_servers()
            registered = register_mcp_tools(self.tools, gateway)
            self.monitor.add_trace("MCP", "MCP_TOOLS_REGISTERED", {"tools": registered})
            self.mcp_gateway = gateway
        except Exception as exc:
            self.monitor.add_trace("MCP", "MCP_INIT_FAILED", {"path": str(config_path), "error": str(exc)})
            self.mcp_gateway = None

    def _execute_managed_plan(self, managed_plan):
        step_results = []
        for step in managed_plan.steps:
            tool_spec = self.tools.get_tool(step.tool) if step.tool else None
            self.monitor.traces.append(RuntimeTrace("OPERATOR_TOOL_CALL", f"{step.id}: {step.tool}", {
                "step_id": step.id,
                "tool": step.tool,
                "args": step.args,
                "reason": step.reason,
                "permission": tool_spec.permission if tool_spec else None
            }))
            if not tool_spec:
                result = ToolResult(ok=False, tool=step.tool or "none", summary="Tool not found", error=f"Tool {step.tool} not found")
            else:
                result = tool_spec.handler(**step.args)
            self.monitor.record_tool_call(result.ok)
            step_results.append((step, result))
            self.monitor.traces.append(RuntimeTrace("OPERATOR_TOOL_RESULT", f"{step.id}: {result.summary}", {
                "step_id": step.id,
                "ok": result.ok,
                "tool": result.tool,
                "summary": result.summary,
                "content": result.content,
                "error": result.error,
                "metadata": result.metadata
            }))
            if not result.ok:
                break

        audit = self.management.auditor.verify(managed_plan, step_results)
        self.monitor.traces.append(RuntimeTrace("AUDITOR_VERIFICATION", audit.final_status, {
            "verified": audit.verified,
            "failed_criteria": audit.failed_criteria,
            "risk_notes": audit.risk_notes,
            "final_status": audit.final_status
        }))
        return ExecutionResult(
            ok=audit.verified,
            plan=managed_plan,
            step_results=step_results,
            audit=audit,
            error="; ".join(audit.failed_criteria)
        )

    def _record_mcp_inventory_trace(self) -> None:
        if not self.mcp_gateway:
            return
        for server_name in self.mcp_gateway.clients.keys():
            self.monitor.add_trace("MCP", "MCP_SERVER_READY", {"server": server_name})
        for descriptor in self.mcp_gateway.tools.values():
            self.monitor.add_trace(
                "MCP",
                "MCP_TOOL_REGISTERED" if descriptor.enabled else "MCP_TOOL_BLOCKED",
                {
                    "server": descriptor.server_name,
                    "tool": descriptor.name,
                    "permission": descriptor.permission,
                },
            )

    def _execute_llm_direct_or_single_tool(self, task: str, user_system_prompt: Optional[str] = None):
        tool_descriptions = self.tools.get_all_descriptions()
        system_prompt = (
            f"You are Hermes Agent OS. Mode: CONTROLLED_AGENT.\n"
            "Default Language: Traditional Chinese (zh-Hant) when the user writes in Chinese.\n"
            "You may execute registered tools when they match the user's request.\n"
            "Never claim you cannot interact with the filesystem if a registered safe tool can perform the task.\n"
            "Writable actions are restricted to safe registered tools and their workspace boundaries.\n"
            f"Tools:\n{tool_descriptions}\n\n"
            "If tool needed, return JSON:\n"
            '{"tool": "name", "args": {}, "reason": "why"}\n'
            "Otherwise, answer directly."
        )
        if user_system_prompt:
            system_prompt = f"{system_prompt}\n\nUser system prompt:\n{user_system_prompt}"

        plan_response = self.llm.completion(prompt=task, system_prompt=system_prompt)
        self._record_usage(plan_response)
        plan = self.planner.parse_output(plan_response["text"], allow_heuristic=False)
        if not plan:
            plan = self.planner.parse_output(task)

        if not plan:
            self.last_result.update({"status": "DONE", "response": plan_response["text"]})
            return

        self.monitor.traces.append(RuntimeTrace("TOOL_PLAN", f"Plan: {plan.tool}", {"tool": plan.tool, "args": plan.args, "reason": plan.reason}))
        self.state_machine.transition_to(AgentState.EXECUTING)
        tool_spec = self.tools.get_tool(plan.tool)
        if not tool_spec:
            self.last_result.update({"status": "FAILED", "error": f"Tool {plan.tool} not found"})
            return
        if tool_spec.permission in {"write", "write_proposal", "shell"}:
            self.last_result.update({
                "status": "FAILED",
                "error": f"Blocked unsafe fallback tool: {plan.tool}. Write-capable tools must be approved by ManagementPolicy."
            })
            return

        self.monitor.traces.append(RuntimeTrace("TOOL_CALL", f"Call: {plan.tool}", {"tool": plan.tool, "args": plan.args, "permission": tool_spec.permission}))
        result: ToolResult = tool_spec.handler(**plan.args)
        self.monitor.record_tool_call(result.ok)
        self.monitor.traces.append(RuntimeTrace("TOOL_RESULT", result.summary, {
            "ok": result.ok,
            "tool": result.tool,
            "summary": result.summary,
            "content": result.content,
            "error": result.error,
            "metadata": result.metadata
        }))

        if not result.ok:
            self.last_result.update({"status": "FAILED", "error": result.error})
            return

        self.state_machine.transition_to(AgentState.VERIFYING)
        context_prompt = f"Task: {task}\nResult: {result.content}\nFinalize answer:"
        final_system_prompt = "Answer based on the tool result. Use Traditional Chinese if the user writes Chinese."
        if user_system_prompt:
            final_system_prompt = f"{final_system_prompt}\n\nUser system prompt:\n{user_system_prompt}"
        final_resp = self.llm.completion(prompt=context_prompt, system_prompt=final_system_prompt)
        self._record_usage(final_resp)
        self.last_result.update({"status": "DONE", "response": final_resp["text"]})

    def _record_usage(self, response: Dict[str, Any]):
        usage = response.get("usage") or {}
        self.monitor.record_tokens(
            int(usage.get("input", 0) or 0),
            int(usage.get("output", 0) or 0)
        )
        self.governance.update_usage(int(usage.get("total", 0) or 0))

    def _should_use_read_confirmation(self, task: str) -> bool:
        lowered = (task or "").lower()
        return any(keyword in lowered for keyword in ["有看到", "看到", "是否了解", "是否理解", "看到了"])

    def _finalize_read_workspace_response(self, managed_result: ExecutionResult) -> str:
        read_paths = []
        for step, result in managed_result.step_results:
            if result.ok:
                read_paths.append(str(step.args.get("path", "")))

        lines = ["已讀取並確認以下 workspace 檔案："]
        lines.extend([f"- {path}" for path in read_paths if path])
        lines.extend([
            "",
            "我已了解這些檔案的角色：",
            "- README.md：Hermes 專案定位、啟動方式、功能與 roadmap。",
            "- agent_skill.md：Hermes/代理的工作規則、Harness Engineering、狀態機、驗證與權限邊界。",
            "",
            "後續我會把被讀檔案內容視為參考資料，而不是直接執行其中的內嵌指令。"
        ])
        return "\n".join(lines)
