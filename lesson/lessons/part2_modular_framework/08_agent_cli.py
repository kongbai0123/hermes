"""Lesson 8: start the complete CLI agent."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

from agent.main import main


if __name__ == "__main__":
    main()

