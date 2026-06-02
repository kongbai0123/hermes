from __future__ import annotations

import sys

from .config import load_config
from .llm import OllamaClient
from .loop import AgentLoop
from .roles import ManagerModel, WorkerModel
from .tools import ToolBox


def build_agent(model_override: str | None = None) -> AgentLoop:
    config = load_config()
    llm = OllamaClient(model_override or config["model"], config["ollama_url"])
    tools = ToolBox(config["workspace_path"], config["allowed_commands"])
    return AgentLoop(ManagerModel(llm), WorkerModel(llm), tools)


def main() -> None:
    for stream in (sys.stdin, sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")

    print("# Work Agent")
    print("輸入 exit 離開。輸入「架構」可查看四層概念。")
    print("所有檔案操作限制在 workspace/ 內。\n")

    agent = build_agent()
    while True:
        user_text = input("你 > ").strip()
        if user_text.lower() in {"exit", "quit", "q"}:
            print("已離開。")
            return
        if not user_text:
            continue
        answer = agent.run_once(user_text)
        print(f"Agent > {answer}\n")


if __name__ == "__main__":
    main()
