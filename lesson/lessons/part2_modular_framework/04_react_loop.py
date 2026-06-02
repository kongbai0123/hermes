"""Lesson 4: minimal ReAct loop with tools."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

from agent.react import ReactAgent


def main() -> None:
    agent = ReactAgent.create()
    question = "請列出 workspace 裡有哪些檔案，並說明 sample_project 可能是做什麼的。"
    print(f"你> {question}\n")
    print(agent.answer(question))


if __name__ == "__main__":
    main()

