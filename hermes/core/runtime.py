import time
from typing import Any, Dict, Optional
from hermes.core.state_machine import StateMachine, AgentState
from hermes.utils.monitor import Monitor
from hermes.core.llm_provider import LLMProvider, OllamaProvider
from hermes.harness.constraints import ConstraintValidator
from hermes.harness.governance import GovernanceManager
from hermes.harness.verifier import Verifier
from hermes.harness.executor import SafeExecutor
from hermes.memory.manager import MemoryManager
from hermes.skills.base import SkillRegistry
from hermes.skills.compiler import SkillCompiler

class HermesRuntime:
    def __init__(self, agent_id: str = "hermes-v1", llm_provider: Optional[LLMProvider] = None):
        self.agent_id = agent_id
        self.monitor = Monitor()
        self.state_machine = StateMachine(on_state_change=self._handle_state_change)
        self.llm = llm_provider or OllamaProvider()
        
        # Harness & Governance
        self.harness = ConstraintValidator()
        self.governance = GovernanceManager()
        self.verifier = Verifier(self.llm)
        self.executor = SafeExecutor(self.harness, self.governance)
        
        # Memory & Skills
        self.memory = MemoryManager()
        self.skills = SkillRegistry()
        self.compiler = SkillCompiler(self.skills)
        self.is_running = False
        self.last_result: Dict[str, Any] = {
            "status": "IDLE",
            "task": None,
            "response": "",
            "error": None
        }

    def _handle_state_change(self, old_state: AgentState, new_state: AgentState):
        print(f"[*] State Transition: {old_state.name} -> {new_state.name}")
        self.monitor.add_trace(
            state=new_state.name,
            action="TRANSITION",
            data={"from": old_state.name}
        )

    def configure_llm(self, llm_provider: LLMProvider):
        self.llm = llm_provider
        self.verifier = Verifier(self.llm)

    def execute_task(self, task: str, user_system_prompt: Optional[str] = None) -> Dict[str, Any]:
        self.is_running = True
        start_time = time.time()
        self.last_result = {
            "status": "RUNNING",
            "task": task,
            "response": "",
            "error": None
        }
        print(f"\n[Task] {task}")
        
        try:
            # 0. Context Retrieval (從記憶提取上下文)
            context = self.memory.get_context(task)
            
            # 1. Planning (透過 LLM 生成計畫，注入上下文)
            self.state_machine.transition_to(AgentState.PLANNING, reason="Decomposing task with memory context")
            
            system_rules = "\n".join(context["system_rules"])
            user_pref = str(context["user_prefs"])
            skills = "\n".join([f"- {s['name']}: {s['description']}" for s in context["available_skills"]])
            
            prompt = f"Context from Memory:\n{context['relevant_knowledge']}\n\nAvailable Skills:\n{skills}\n\nTask: {task}"
            custom_rules = f"\nUser System Prompt: {user_system_prompt.strip()}" if user_system_prompt and user_system_prompt.strip() else ""
            system_prompt = f"System Rules: {system_rules}\nUser Preference: {user_pref}{custom_rules}\nDefault Language: Traditional Chinese (zh-Hant) when the user writes in Chinese. Avoid Simplified Chinese unless explicitly requested.\n\nProvide a helpful response and a concise technical plan when useful. Use available skills if applicable."
            
            plan_response = self.llm.completion(prompt=prompt, system_prompt=system_prompt)
            
            self.monitor.record_tokens(
                plan_response["usage"]["input"], 
                plan_response["usage"]["output"]
            )
            print(f"[Plan] {plan_response['text'][:100]}...")

            # 2. Executing
            self.state_machine.transition_to(AgentState.EXECUTING, reason="Executing validated steps")
            # ... 執行邏輯 ...
            time.sleep(0.3)
            user_response = plan_response["text"]
            
            # 3. Verifying
            self.state_machine.transition_to(AgentState.VERIFYING, reason="Validating results")
            success = True 
            
            if success:
                self.state_machine.transition_to(AgentState.DONE, reason="Task completed")
                self.last_result = {
                    "status": AgentState.DONE.name,
                    "task": task,
                    "response": user_response,
                    "error": None
                }
                self.monitor.add_trace(
                    state=AgentState.DONE.name,
                    action="USER_RESPONSE",
                    data={"response": user_response}
                )
                # 4. Consolidate Memory (將經驗存入記憶)
                self.memory.consolidate_session(task, user_response)
            else:
                self.state_machine.transition_to(AgentState.RECOVERING, reason="Verification failed")
                self.last_result = {
                    "status": AgentState.RECOVERING.name,
                    "task": task,
                    "response": "",
                    "error": "Verification failed"
                }

        except Exception as e:
            self.monitor.record_error("RUNTIME_ERROR", str(e))
            self.state_machine.transition_to(AgentState.FAILED, reason=f"Exception: {str(e)}")
            self.last_result = {
                "status": AgentState.FAILED.name,
                "task": task,
                "response": "",
                "error": str(e)
            }
        
        finally:
            self.is_running = False
            duration = time.time() - start_time
            self.monitor.record_latency("total_execution", duration)
            print(f"[+] Task finished in {duration:.2f}s")
            return self.last_result

    def get_status(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "current_state": self.state_machine.current_state.name,
            "is_running": self.is_running,
            "metrics": self.monitor.get_summary(),
            "last_result": self.last_result
        }
