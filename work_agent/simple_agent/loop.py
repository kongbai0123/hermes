from __future__ import annotations

from .bounded_loop import BoundedLoopController, LoopLimits
from .roles import ExplainWorker, ManagerModel, WorkerModel
from .tools import ToolBox


class AgentLoop:
    def __init__(
        self,
        manager: ManagerModel,
        worker: WorkerModel,
        tools: ToolBox,
        limits: LoopLimits | None = None,
    ) -> None:
        self.manager = manager
        self.worker = worker
        self.tools = tools
        self.explainer = ExplainWorker(worker.llm)
        self.controller = BoundedLoopController(manager, worker, tools, limits)

    def run_once(self, user_text: str) -> str:
        result = self.run_once_structured(user_text)
        return str(result["answer"])

    def run_once_structured(self, user_text: str) -> dict:
        if user_text.strip() in {"架構", "說明架構", "agent loop"}:
            answer = self.explainer.explain_architecture()
            return {
                "answer": answer,
                "decision": {
                    "plan": "說明目前架構。",
                    "worker": "explain",
                    "tool": "none",
                    "args": {},
                },
                "observation": {
                    "ok": True,
                    "tool": "none",
                    "content": "Architecture explanation requested.",
                    "formatted": "[OK] none: Architecture explanation requested.",
                },
            }

        print("\n[Agent Loop] 接收任務")
        result = self.controller.run(user_text)
        decision = result["decision"]
        observation = result["observation"]
        print("[Loop Controller] Bounded closed loop 啟動")
        print(f"[Loop Controller] Stop reason: {result['stop_reason']}")
        print(f"[Loop Controller] Steps: {result['loop']['steps']}/{result['loop']['max_steps']}")
        print(f"[Manager Model] Plan: {decision['plan']}")
        print(f"[Manager Model] Worker: {decision['worker']}")
        print(f"[Manager Model] Tool: {decision['tool']} {decision['args']}")
        print(f"[Tools] Observation: {observation['formatted']}")
        print("[Worker Model] 整理回覆\n")
        return result
