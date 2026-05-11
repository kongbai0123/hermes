import time
from typing import Any, Dict, Optional, List
from hermes.core.state_machine import StateMachine, AgentState
from hermes.core.types import ToolPlan, ToolResult, RuntimeTrace, CapabilityPolicy
from hermes.core.tool_planner import ToolPlanner
from hermes.core.llm_provider import LLMProvider, OllamaProvider, MockLLMProvider
from hermes.harness.constraints import ConstraintValidator
from hermes.harness.executor import SafeExecutor
from hermes.harness.tools import ToolRegistry
from hermes.utils.monitor import Monitor

class HermesRuntime:
    """
    Hermes Agent Runtime: 負責代理的狀態管理與任務執行閉環。
    """
    def __init__(self, agent_id: str = "hermes-v1", llm_provider: Optional[LLMProvider] = None):
        self.agent_id = agent_id
        self.monitor = Monitor()
        self.state_machine = StateMachine(on_state_change=self._handle_state_change)
        self.llm = llm_provider or OllamaProvider()
        
        # 安全與工具體系
        self.constraints = ConstraintValidator()
        self.executor = SafeExecutor(self.constraints)
        self.registry = ToolRegistry(self.executor)
        self.planner = ToolPlanner(self.registry)
        self.policy = CapabilityPolicy() # v1 預設 Read-Only
        
        self.is_running = False
        self.last_result = {"status": "IDLE", "task": "", "response": "", "error": ""}

    def _handle_state_change(self, old_state: AgentState, new_state: AgentState):
        print(f"[*] State Transition: {old_state.name} -> {new_state.name}")
        self.monitor.add_trace(
            state=new_state.name,
            action="TRANSITION",
            data={"from": old_state.name}
        )

    def execute_task(self, task: str):
        """執行任務閉環流程"""
        self.is_running = True
        self.last_result = {"status": "RUNNING", "task": task, "response": "", "error": ""}
        start_time = time.time()
        
        # 紀錄使用者指令
        self.monitor.traces.append(RuntimeTrace(event_type="USER_CMD", message=f"User Task: {task}", payload={"task": task}))

        try:
            # 1. Routing & Planning
            self.state_machine.transition_to(AgentState.PLANNING, reason="Determining tool necessity")
            
            tool_descriptions = self.registry.get_all_descriptions()
            system_prompt = (
                f"You are Hermes Agent OS. Current Mode: READ_ONLY.\n"
                f"Available Tools:\n{tool_descriptions}\n\n"
                "If you need to read a file or list a directory to answer, return a JSON object:\n"
                '{"tool": "tool_name", "args": {"arg_name": "value"}, "reason": "why"}\n'
                "Otherwise, answer directly."
            )
            
            # 第一階段推理：判斷是否需要工具
            self.monitor.traces.append(RuntimeTrace(event_type="PLAN_REQUEST", message="LLM planning request", payload={"task": task}))
            plan_response = self.llm.completion(prompt=task, system_prompt=system_prompt)
            raw_plan_text = plan_response["text"]
            
            # 解析工具計畫
            plan = self.planner.parse_output(raw_plan_text)
            
            if plan:
                # 2. Executing Tool
                self.monitor.traces.append(RuntimeTrace(event_type="TOOL_PLAN", message=f"Tool Plan: {plan.tool}", payload={"tool": plan.tool, "args": plan.args, "reason": plan.reason}))
                self.state_machine.transition_to(AgentState.EXECUTING, reason=f"Calling {plan.tool}")
                
                tool_spec = self.registry.get_tool(plan.tool)
                if tool_spec:
                    self.monitor.traces.append(RuntimeTrace(event_type="TOOL_CALL", message=f"Executing {plan.tool}", payload={"args": plan.args}))
                    result: ToolResult = tool_spec.handler(**plan.args)
                    
                    # 紀錄工具結果
                    result_payload = {"ok": result.ok, "summary": result.summary, "error": result.error, "metadata": result.metadata}
                    self.monitor.traces.append(RuntimeTrace(event_type="TOOL_RESULT", message=result.summary, payload=result_payload))
                    
                    # 3. Synthesizing Answer (閉環)
                    if result.ok:
                        self.state_machine.transition_to(AgentState.VERIFYING, reason="Synthesizing final answer from tool content")
                        context_prompt = f"User asked: {task}\n\nTool '{plan.tool}' returned:\n{result.content}\n\nBased on this information, provide the final answer."
                        final_response = self.llm.completion(prompt=context_prompt, system_prompt="Synthesize the final answer based on the tool output.")
                        self.last_result.update({"status": "DONE", "response": final_response["text"]})
                        self.monitor.traces.append(RuntimeTrace(event_type="LLM_FINAL", message="Task completed successfully", payload={"response": final_response["text"]}))
                    else:
                        self.last_result.update({"status": "FAILED", "error": result.error})
                        self.monitor.traces.append(RuntimeTrace(event_type="HERMES_ERROR", message=f"Tool execution failed: {result.error}"))
            else:
                # 直接回答路徑
                self.last_result.update({"status": "DONE", "response": raw_plan_text})
                self.monitor.traces.append(RuntimeTrace(event_type="LLM_FINAL", message="Direct answer generated", payload={"response": raw_plan_text}))

            self.state_machine.transition_to(AgentState.DONE, reason="Task iteration finished")

        except Exception as e:
            err_msg = f"Runtime Crash: {str(e)}"
            self.monitor.record_error("RUNTIME_ERROR", err_msg)
            self.state_machine.transition_to(AgentState.FAILED, reason=err_msg)
            self.last_result.update({"status": "FAILED", "error": err_msg})
            self.monitor.traces.append(RuntimeTrace(event_type="HERMES_ERROR", message=err_msg))
        
        finally:
            self.is_running = False
            duration = time.time() - start_time
            self.monitor.record_latency("total_execution", duration)

    def get_status(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "current_state": self.state_machine.current_state.name,
            "is_running": self.is_running,
            "last_result": self.last_result,
            "metrics": self.monitor.get_summary()
        }
