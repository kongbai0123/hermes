# External Chat Bridge Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Hermes external chat loop that can send a message to a web GPT bridge, wait for a reply, capture that reply, and use it as the next Hermes observation.

**Architecture:** Add a small `ExternalChatBridge` interface with a deterministic fake implementation for tests and a clipboard-backed placeholder for real web automation wiring. Route user requests through `external_chat`, governed as `MCP_GOVERNED / external_state`, then expose the received external reply through `Observation`.

**Tech Stack:** Python, pytest, existing Hermes `ToolBox`, `ManagerModel`, `PolicyGate`, `WorkSkillRouter`.

---

### Task 1: External Chat Bridge Contract

**Files:**
- Create: `work_agent/simple_agent/external_chat.py`
- Test: `work_agent/tests/test_external_chat.py`

- [ ] **Step 1: Write the failing bridge tests**

```python
from simple_agent.external_chat import FakeExternalChatBridge


def test_fake_external_chat_bridge_records_message_and_returns_reply() -> None:
    bridge = FakeExternalChatBridge({"HI": "HI，很高興為你服務，請問有甚麼可以幫忙的嗎?"})

    result = bridge.send_and_receive("HI", target="chatgpt_web")

    assert result.ok is True
    assert result.reply == "HI，很高興為你服務，請問有甚麼可以幫忙的嗎?"
    assert bridge.sent_messages == [("chatgpt_web", "HI")]
```

- [ ] **Step 2: Implement the contract**

```python
@dataclass(frozen=True)
class ExternalChatResult:
    ok: bool
    target: str
    message: str
    reply: str
    status: str
    error: str | None = None
```

### Task 2: ToolBox external_chat

**Files:**
- Modify: `work_agent/simple_agent/tools.py`
- Test: `work_agent/tests/test_tools.py`

- [ ] **Step 1: Add ToolBox tests**

```python
def test_external_chat_sends_and_receives_reply(tmp_path: Path) -> None:
    bridge = FakeExternalChatBridge({"HI": "HI，很高興為你服務"})
    tools = ToolBox(str(tmp_path), ["python --version"], external_chat_bridge=bridge)

    result = tools.external_chat("HI", target="chatgpt_web")

    assert result.ok is True
    assert "HI，很高興為你服務" in result.content
```

- [ ] **Step 2: Implement ToolBox.external_chat and execute routing**

```python
def external_chat(self, message: str, target: str = "chatgpt_web") -> Observation:
    result = self.external_chat_bridge.send_and_receive(message, target=target)
    ...
```

### Task 3: Manager and Policy Routing

**Files:**
- Modify: `work_agent/simple_agent/roles.py`
- Modify: `work_agent/simple_agent/bounded_loop.py`
- Modify: `work_agent/simple_agent/work_execution.py`
- Test: `work_agent/tests/test_roles.py`
- Test: `work_agent/tests/test_bounded_loop.py`
- Test: `work_agent/tests/test_work_execution.py`

- [ ] **Step 1: Add failing routing tests**

```python
def test_manager_routes_gpt_web_message_to_external_chat() -> None:
    decision = manager.decide("請 Hermes 到 GPT 下達 HI 並讀回回答")
    assert decision.tool == "external_chat"
    assert decision.args["message"] == "HI"
```

- [ ] **Step 2: Add `external_chat` to router external tools**

```python
EXTERNAL_TOOLS = {"proxy_fetch", "open_browser", "external_codex", "external_chat", ...}
```

- [ ] **Step 3: Add `external_chat` to PolicyGate external agent tools**

```python
EXTERNAL_AGENT_TOOLS = {"external_codex", "external_chat"}
```

### Task 4: End-to-End Bounded Loop

**Files:**
- Test: `work_agent/tests/test_bounded_loop.py`

- [ ] **Step 1: Add closed-loop test**

```python
def test_bounded_loop_uses_external_chat_reply_as_observation(tmp_path: Path) -> None:
    bridge = FakeExternalChatBridge({"HI": "HI，很高興為你服務"})
    ...
    assert result["observation"]["tool"] == "external_chat"
    assert "HI，很高興為你服務" in result["answer"]
```

- [ ] **Step 2: Run focused tests**

Run: `python -m pytest tests/test_external_chat.py tests/test_tools.py tests/test_roles.py tests/test_bounded_loop.py tests/test_work_execution.py -q`

Expected: all tests pass.

### Task 5: Full Verification

**Files:**
- No new files.

- [ ] **Step 1: Run backend suite**

Run: `python -m pytest tests -q`

Expected: all tests pass.
