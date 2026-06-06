from __future__ import annotations

import json
from typing import Protocol


class GuiRunner(Protocol):
    def observe(self) -> str:
        """Return a compact JSON description of the current GUI state."""

    def verify(self, condition: str) -> str:
        """Return a compact JSON verification result for a GUI condition."""


class MockGuiRunner:
    """Deterministic GUI runner used for policy, trace, and integration tests."""

    def observe(self) -> str:
        payload = {
            "status": "observed",
            "runner": "mock",
            "screen_id": "mock_screen_001",
            "visible_elements": [
                {
                    "id": "chat_prompt",
                    "label": "ChatGPT prompt",
                    "role": "textbox",
                    "bounds": {"x": 370, "y": 600, "width": 720, "height": 52},
                },
                {
                    "id": "send_button",
                    "label": "Send",
                    "role": "button",
                    "bounds": {"x": 1088, "y": 606, "width": 44, "height": 44},
                },
            ],
        }
        return json.dumps(payload, ensure_ascii=False)

    def verify(self, condition: str) -> str:
        safe_condition = (condition or "").strip()
        known_conditions = {
            "chat_prompt_visible": True,
            "send_button_visible": True,
            "external_reply_visible": False,
        }
        payload = {
            "status": "verified",
            "runner": "mock",
            "condition": safe_condition,
            "matched": known_conditions.get(safe_condition, False),
        }
        return json.dumps(payload, ensure_ascii=False)
