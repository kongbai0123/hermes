"""Lesson 5: read and search code inside the allowed workspace."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

from agent.tools import read_file, search_files


def main() -> None:
    print("Search for divide:")
    print(search_files({"pattern": "divide", "path": "."}).to_observation())
    print("\nRead calculator.py:")
    print(read_file({"path": "sample_project/calculator.py"}).to_observation())


if __name__ == "__main__":
    main()

