"""CLI entry point for the local Codex-like agent."""

from __future__ import annotations

import sys
from pathlib import Path

if __package__ is None or __package__ == "":
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from agent.react import ReactAgent
from agent.tools import WORKSPACE_ROOT


def main() -> None:
    print("Local Codex-like Agent")
    print(f"Allowed workspace: {WORKSPACE_ROOT}")
    print("Type /exit to quit.\n")

    agent = ReactAgent.create()
    while True:
        try:
            user_message = input("你> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye.")
            return
        if not user_message:
            continue
        if user_message in {"/exit", "/quit"}:
            print("Bye.")
            return

        answer = agent.answer(user_message)
        print("\nAgent>")
        print(answer)
        print()


if __name__ == "__main__":
    main()

