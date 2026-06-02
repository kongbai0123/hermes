"""Lesson 3: call simple tools from Python."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

from agent.tools import calculate, get_current_time, list_files


def main() -> None:
    print("Tool: get_current_time")
    print(get_current_time({}).to_observation())
    print()

    print("Tool: calculate")
    print(calculate({"expression": "2 + 3 * 4"}).to_observation())
    print()

    print("Tool: list_files")
    print(list_files({"path": "."}).to_observation())


if __name__ == "__main__":
    main()

