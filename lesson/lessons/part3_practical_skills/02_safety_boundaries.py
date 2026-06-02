"""Part 3-2: test safety boundaries before trusting an agent."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

from agent.tools import read_file, run_command


def main() -> None:
    checks = [
        ("讀取 workspace 內檔案", read_file({"path": "sample_project/calculator.py"})),
        ("拒絕讀取 workspace 外檔案", read_file({"path": "../README.md"})),
        ("拒絕未允許命令", run_command({"command": "Remove-Item sample_project/calculator.py"})),
        ("允許測試命令", run_command({"command": "python -m unittest discover -s sample_project"})),
    ]
    for title, result in checks:
        print(f"\n=== {title} ===")
        print(result.to_observation())


if __name__ == "__main__":
    main()

