from simple_agent.roles import ManagerDecision, ManagerModel, WorkerModel
from simple_agent.tools import Observation


class RefusalLLM:
    def chat(self, _messages):
        return "我無法直接操作您電腦桌面上安裝的軟體或執行本地系統指令。"


def test_worker_uses_observation_instead_of_generic_local_refusal() -> None:
    worker = WorkerModel(RefusalLLM())  # type: ignore[arg-type]
    decision = ManagerDecision(
        "使用 open_browser 開啟 YouTube。",
        "browser",
        "open_browser",
        {"url": "https://www.youtube.com", "browser": "chrome"},
    )
    observation = Observation(True, "open_browser", "已請 chrome 開啟：https://www.youtube.com")

    answer = worker.respond("請開啟 YouTube", decision, observation)

    assert "無法直接操作" not in answer
    assert "雲端" not in answer
    assert "已執行工具" in answer
    assert "open_browser" in answer


def test_manager_fallback_routes_external_codex_work_to_agent_tool() -> None:
    manager = ManagerModel(RefusalLLM())  # type: ignore[arg-type]

    decision = manager.decide("麻煩幫我執行codex，評估hermes功能並提出優化")

    assert decision.tool == "external_codex"
    assert decision.worker == "external"
    assert decision.args["mode"] == "self_optimization_discussion"
    assert "hermes" in decision.args["topic"].lower()


def test_manager_fallback_routes_gpt_web_message_to_external_chat() -> None:
    manager = ManagerModel(RefusalLLM())  # type: ignore[arg-type]

    decision = manager.decide("請 Hermes 到 GPT 下達 HI 並讀回回答")

    assert decision.tool == "external_chat"
    assert decision.worker == "external"
    assert decision.args["target"] == "chatgpt_web"
    assert decision.args["message"] == "HI"


def test_manager_fallback_routes_multi_turn_gpt_web_work_to_external_chat_loop() -> None:
    manager = ManagerModel(RefusalLLM())  # type: ignore[arg-type]

    decision = manager.decide("請 Hermes 到 GPT 下達 HI，並跟外部 model 來回聊天 3 輪")

    assert decision.tool == "external_chat_loop"
    assert decision.worker == "external"
    assert decision.args["target"] == "chatgpt_web"
    assert decision.args["message"] == "HI"
    assert decision.args["max_turns"] == "3"
