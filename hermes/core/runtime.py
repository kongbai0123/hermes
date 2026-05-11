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
        
        # 初始化安全工具體系
        self.constraints = ConstraintValidator()
        self.executor = SafeExecutor(self.constraints)
        self.tools = ToolRegistry(self.executor)
        self.planner = ToolPlanner(self.tools)
        
        self.is_running = False
        self.last_result = {"status": "IDLE", "task": "", "response": "", "error": "", "trace": []}

    def _handle_state_change(self, old_state: AgentState, new_state: AgentState):
        self.monitor.add_trace(state=new_state.name, action="TRANSITION", data={"from": old_state.name})

    def execute_task(self, task: str, **llm_config):
        self.is_running = True
        self.last_result = {"status": "RUNNING", "task": task, "response": "", "error": "", "trace": []}
        start_time = time.time()
        
        # 紀錄初始指令
        self.monitor.traces.append(RuntimeTrace(event_type="USER_CMD", message=f"User Task: {task}", payload={"task": task}))

        try:
            # 1. Planning 階段
            self.state_machine.transition_to(AgentState.PLANNING)
            
            tool_descriptions = self.tools.get_all_descriptions()
            system_prompt = (
                f"You are Hermes Agent OS. Current Mode: READ_ONLY.\n"
                f"Available Tools:\n{tool_descriptions}\n\n"
                "If you need to read a file or list a directory to answer, return a JSON object:\n"
                '{"tool": "tool_name", "args": {"path": "value"}, "reason": "why"}\n'
                "Otherwise, answer the user directly."
            )
            
            plan_response = self.llm.completion(prompt=task, system_prompt=system_prompt, **llm_config)
            raw_text = plan_response["text"]
            
            # 解析是否需要工具
            plan = self.planner.parse_output(raw_text)
            
            if plan:
                # 2. Executing 階段
                self.monitor.traces.append(RuntimeTrace(event_type="TOOL_PLAN", message=f"Plan: {plan.tool}", payload={"tool": plan.tool, "path": plan.args.get("path")}))
                self.state_machine.transition_to(AgentState.EXECUTING)
                
                tool_spec = self.tools.get_tool(plan.tool)
                if tool_spec:
                    self.monitor.traces.append(RuntimeTrace(event_type="TOOL_CALL", message=f"Executing {plan.tool}", payload=plan.args))
                    result: ToolResult = tool_spec.handler(**plan.args)
                    
                    # 紀錄工具執行結果
                    result_payload = {"ok": result.ok, "summary": result.summary, "error": result.error, "metadata": result.metadata}
                    self.monitor.traces.append(RuntimeTrace(event_type="TOOL_RESULT", message=result.summary, payload=result_payload))
                    
                    if result.ok:
                        # 3. Verifying / Finalizing 階段 (注入工具結果進行再推理)
                        self.state_machine.transition_to(AgentState.VERIFYING)
                        context_prompt = f"User asked: {task}\n\nTool '{plan.tool}' returned:\n{result.content}\n\nBased on this information, provide the final answer."
                        final_response = self.llm.completion(prompt=context_prompt, system_prompt="Answer based on tool output.")
                        self.last_result.update({"status": "DONE", "response": final_response["text"]})
                        self.monitor.traces.append(RuntimeTrace(event_type="LLM_FINAL", message="Closed-loop response ready", payload={"response": final_response["text"]}))
                    else:
                        self.last_result.update({"status": "FAILED", "error": result.error})
                else:
                    self.last_result.update({"status": "FAILED", "error": f"Tool {plan.tool} not found."})
            else:
                # 無需工具，直接回答
                self.last_result.update({"status": "DONE", "response": raw_text})
                self.monitor.traces.append(RuntimeTrace(event_type="LLM_FINAL", message="Direct answer", payload={"response": raw_text}))

            self.state_machine.transition_to(AgentState.DONE)

        except Exception as e:
            self.state_machine.transition_to(AgentState.FAILED)
            self.last_result.update({"status": "FAILED", "error": str(e)})
            self.monitor.traces.append(RuntimeTrace(event_type="HERMES_ERROR", message=str(e)))
        
        finally:
            self.is_running = False
            self.last_result["trace"] = self.monitor.get_serializable_traces()
            self.monitor.record_latency("execution", time.time() - start_time)

    def get_status(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "current_state": self.state_machine.current_state.name,
            "is_running": self.is_running,
            "last_result": self.last_result,
            "metrics": self.monitor.get_summary()
        }
