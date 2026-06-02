"""Lesson 1: talk to your local Ollama model."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

from agent.llm import generate


def main() -> None:
    prompt = "請用繁體中文用三句話說明：什麼是 AI agent？"
    print(f"User: {prompt}\n")
    print("Assistant:")
    for chunk in generate(prompt, stream=True):
        print(chunk, end="", flush=True)
    print()


if __name__ == "__main__":
    main()

