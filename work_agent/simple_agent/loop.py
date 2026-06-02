from __future__ import annotations

from .roles import ExplainWorker, ManagerModel, WorkerModel
from .tools import Observation, ToolBox


class AgentLoop:
    def __init__(self, manager: ManagerModel, worker: WorkerModel, tools: ToolBox) -> None:
        self.manager = manager
        self.worker = worker
        self.tools = tools
        self.explainer = ExplainWorker(worker.llm)

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
        decision = self.manager.decide(user_text)
        print(f"[Manager Model] Plan: {decision.plan}")
        print(f"[Manager Model] Worker: {decision.worker}")
        print(f"[Manager Model] Tool: {decision.tool} {decision.args}")

        if decision.tool == "none":
            observation = Observation(
                True,
                "none",
                "未使用工具。此版本已接上的工具是讀檔、列檔、搜尋文字與白名單命令；"
                "尚未接上 Browser、API、Proxy 或即時網路代理工具。",
            )
        else:
            observation = self.tools.execute(decision.tool, **decision.args)

        print(f"[Tools] Observation: {observation.format()}")
        print("[Worker Model] 整理回覆\n")
        answer = self.worker.respond(user_text, decision, observation)
        return {
            "answer": answer,
            "decision": {
                "plan": decision.plan,
                "worker": decision.worker,
                "tool": decision.tool,
                "args": dict(decision.args),
            },
            "observation": {
                "ok": observation.ok,
                "tool": observation.tool,
                "content": observation.content,
                "formatted": observation.format(),
            },
        }
