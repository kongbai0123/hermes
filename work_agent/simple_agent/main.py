from __future__ import annotations

import sys

from .config import load_config
from .bounded_loop import LoopLimits
from .llm import OllamaClient
from .loop import AgentLoop
from .roles import ManagerModel, WorkerModel
from .tools import ToolBox
from .external_chat import WindowsClipboardExternalChatBridge
from .gui_agent import MockGuiRunner, WindowsGuiRunner


def build_external_chat_bridge(config: dict):
    bridge_config = dict(config.get("external_chat_bridge", {}))
    if not bridge_config.get("enabled", False):
        return None
    if bridge_config.get("mode") != "windows_clipboard":
        return None
    return WindowsClipboardExternalChatBridge(
        window_title=str(bridge_config.get("window_title", "Google Chrome")),
        wait_seconds=int(bridge_config.get("wait_seconds", 20)),
    )


def build_gui_runner(config: dict):
    runner_config = dict(config.get("gui_runner", {}))
    if not runner_config.get("enabled", False):
        return MockGuiRunner()
    if runner_config.get("mode") != "windows":
        return MockGuiRunner()
    screenshot_dir = runner_config.get("screenshot_dir", "trace/gui")
    return WindowsGuiRunner(screenshot_dir=str(screenshot_dir))


def build_agent(model_override: str | None = None) -> AgentLoop:
    config = load_config()
    llm = OllamaClient(model_override or config["model"], config["ollama_url"])
    tools = ToolBox(
        config["workspace_path"],
        config["allowed_commands"],
        allowed_proxy_domains=list(config.get("allowed_proxy_domains", [])),
        allowed_browser_domains=list(config.get("allowed_browser_domains", [])),
        external_chat_bridge=build_external_chat_bridge(config),
        gui_runner=build_gui_runner(config),
    )
    limits = LoopLimits(
        max_steps=int(config.get("max_steps", 6)),
        max_replans=int(config.get("max_replans", 2)),
        max_tool_failures=int(config.get("max_tool_failures", 2)),
        max_same_action_repeat=int(config.get("max_same_action_repeat", 1)),
        default_capability=str(config.get("default_capability", "read_only")),
    )
    return AgentLoop(ManagerModel(llm), WorkerModel(llm), tools, limits)


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
