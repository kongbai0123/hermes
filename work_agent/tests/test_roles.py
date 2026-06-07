from simple_agent.roles import ManagerDecision, ManagerModel, WorkerModel
from simple_agent.tools import Observation


class RefusalLLM:
    def chat(self, _messages):
        return "我無法直接操作您電腦桌面上安裝的軟體或執行本地系統指令。"


class BrowserFirstLLM:
    def chat(self, _messages):
        return (
            '{"plan":"Observation of external web page UI","worker":"external",'
            '"tool":"open_browser","args":{"url":"https://chat.openai.com/","browser":"chrome"}}'
        )


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


def test_manager_fallback_routes_self_development_to_self_improve() -> None:
    manager = ManagerModel(RefusalLLM())  # type: ignore[arg-type]

    decision = manager.decide("請 Hermes 修改、優化、開發自己的程式能力")

    assert decision.tool == "self_improve"
    assert decision.worker == "self_development"
    assert decision.args["mode"] == "proposal_only"
    assert decision.args["scope"] == "simple_agent"
    assert "Hermes" in decision.args["goal"]


def test_manager_routes_external_ui_observation_to_gui_observe_before_llm() -> None:
    manager = ManagerModel(BrowserFirstLLM())  # type: ignore[arg-type]

    decision = manager.decide("請 Hermes 觀察外部 GPT 畫面並回報可見 UI")

    assert decision.tool == "gui_observe"
    assert decision.worker == "gui"


def test_manager_routes_external_ui_verification_to_gui_verify_before_llm() -> None:
    manager = ManagerModel(BrowserFirstLLM())  # type: ignore[arg-type]

    decision = manager.decide("請 Hermes 驗證外部 GPT 的 chat_prompt_visible")

    assert decision.tool == "gui_verify"
    assert decision.worker == "gui"
    assert decision.args["condition"] == "chat_prompt_visible"


def test_manager_routes_external_ui_click_to_gui_click_before_llm() -> None:
    manager = ManagerModel(BrowserFirstLLM())  # type: ignore[arg-type]

    decision = manager.decide("請 Hermes 點擊外部 GPT 送出按鈕")

    assert decision.tool == "gui_click"
    assert decision.worker == "gui"
    assert decision.args["target"] == "send_button"


def test_manager_routes_antigravity_text_input_to_gui_type_text_before_llm() -> None:
    manager = ManagerModel(BrowserFirstLLM())  # type: ignore[arg-type]

    decision = manager.decide("請 Hermes 在 antigravity 上打 HI")

    assert decision.tool == "gui_type_text"
    assert decision.worker == "gui"
    assert decision.args["target"] == "window:antigravity"
    assert decision.args["text"] == "HI"


def test_manager_routes_genshin_launch_to_app_launch_before_llm() -> None:
    manager = ManagerModel(BrowserFirstLLM())  # type: ignore[arg-type]

    decision = manager.decide("請 Hermes 啟動桌面上原神")

    assert decision.tool == "app_launch"
    assert decision.worker == "gui"
    assert decision.args["shortcut"] == "原神"
