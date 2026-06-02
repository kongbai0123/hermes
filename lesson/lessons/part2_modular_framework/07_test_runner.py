"""Lesson 7: run an allowed test command and inspect output."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

from agent.tools import run_command


def main() -> None:
    result = run_command({"command": "python -m unittest discover -s sample_project"})
    print(result.to_observation())


if __name__ == "__main__":
    main()

