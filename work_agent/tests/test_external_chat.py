import json

from simple_agent.external_chat import (
    FakeExternalChatBridge,
    UnconfiguredExternalChatBridge,
    run_external_chat_loop,
)


def test_fake_external_chat_bridge_records_message_and_returns_reply() -> None:
    bridge = FakeExternalChatBridge({"HI": "HI，很高興為你服務，請問有甚麼可以幫忙的嗎?"})

    result = bridge.send_and_receive("HI", target="chatgpt_web")

    assert result.ok is True
    assert result.reply == "HI，很高興為你服務，請問有甚麼可以幫忙的嗎?"
    assert result.status == "completed"
    assert bridge.sent_messages == [("chatgpt_web", "HI")]


def test_fake_external_chat_bridge_uses_default_reply_when_message_not_mapped() -> None:
    bridge = FakeExternalChatBridge(default_reply="收到外部 GPT 回覆")

    result = bridge.send_and_receive("我想請你幫我了解今天天氣", target="chatgpt_web")

    assert result.ok is True
    assert result.reply == "收到外部 GPT 回覆"
    assert bridge.sent_messages == [("chatgpt_web", "我想請你幫我了解今天天氣")]


def test_unconfigured_external_chat_bridge_returns_handoff_payload() -> None:
    bridge = UnconfiguredExternalChatBridge()

    result = bridge.send_and_receive("HI", target="chatgpt_web")

    assert result.ok is True
    assert result.status == "handoff_ready"
    assert "chatgpt_web" in result.reply
    assert "HI" in result.reply


def test_external_chat_loop_keeps_turns_until_max_turns() -> None:
    bridge = FakeExternalChatBridge(
        {
            "HI": "HI，很高興為你服務，請問有甚麼可以幫忙的嗎?",
        },
        default_reply="下一輪回覆：我會繼續補充 Hermes 可執行的建議。",
    )

    result = run_external_chat_loop(bridge, "HI", target="chatgpt_web", max_turns=2)

    assert result.ok is True
    assert result.status == "completed"
    assert result.turn_count == 2
    assert result.turns[0].sent == "HI"
    assert result.turns[0].received == "HI，很高興為你服務，請問有甚麼可以幫忙的嗎?"
    assert "上一輪回覆" in result.turns[1].sent
    assert result.turns[1].received == "下一輪回覆：我會繼續補充 Hermes 可執行的建議。"
    assert bridge.sent_messages[0] == ("chatgpt_web", "HI")
    assert len(bridge.sent_messages) == 2


def test_external_chat_loop_serializes_turn_history() -> None:
    bridge = FakeExternalChatBridge({"HI": "收到"})

    result = run_external_chat_loop(bridge, "HI", target="chatgpt_web", max_turns=1)
    payload = json.loads(result.to_json())

    assert payload["target"] == "chatgpt_web"
    assert payload["turn_count"] == 1
    assert payload["turns"][0]["sent"] == "HI"
    assert payload["turns"][0]["received"] == "收到"
