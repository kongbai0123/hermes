"""Conversation memory helpers."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Message:
    role: str
    content: str


@dataclass
class ConversationMemory:
    system_prompt: str
    messages: list[Message] = field(default_factory=list)
    max_messages: int = 12

    def add(self, role: str, content: str) -> None:
        self.messages.append(Message(role=role, content=content))
        if len(self.messages) > self.max_messages:
            self.messages = self.messages[-self.max_messages :]

    def render(self, current_user_message: str | None = None) -> str:
        lines = [f"System:\n{self.system_prompt.strip()}", ""]
        for message in self.messages:
            lines.append(f"{message.role.title()}:\n{message.content.strip()}")
            lines.append("")
        if current_user_message:
            lines.append(f"User:\n{current_user_message.strip()}")
            lines.append("")
        lines.append("Assistant:")
        return "\n".join(lines)

