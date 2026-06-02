"""Lesson 2: keep conversation history in the prompt."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

from agent.llm import generate
from agent.memory import ConversationMemory


def main() -> None:
    memory = ConversationMemory(
        system_prompt="你是一個簡潔的繁體中文 AI agent 教學助手。"
    )
    print("Memory chat. Type /exit to quit.")
    while True:
        user_message = input("你> ").strip()
        if user_message in {"/exit", "/quit"}:
            break
        prompt = memory.render(user_message)
        answer = str(generate(prompt, temperature=0.2)).strip()
        print(f"Agent> {answer}\n")
        memory.add("user", user_message)
        memory.add("assistant", answer)


if __name__ == "__main__":
    main()

