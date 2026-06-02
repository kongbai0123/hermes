"""Part 3-4: a deterministic debug workflow without modifying files."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

from agent.tools import propose_patch, read_file, run_command, search_files


PATCH = """--- a/sample_project/calculator.py
+++ b/sample_project/calculator.py
@@
 def divide(a, b):
-    # Intentional bug for lesson 7: this should reject division by zero clearly.
+    if b == 0:
+        raise ValueError("division by zero")
     return a / b
"""


def main() -> None:
    steps = [
        ("1. 跑測試取得錯誤", run_command({"command": "python -m unittest discover -s sample_project"})),
        ("2. 搜尋失敗函式", search_files({"pattern": "divide", "path": "."})),
        ("3. 讀取目標檔案", read_file({"path": "sample_project/calculator.py"})),
        ("4. 產生修正 patch", propose_patch({"path": "sample_project/calculator.py", "patch": PATCH})),
    ]
    for title, result in steps:
        print(f"\n=== {title} ===")
        print(result.to_observation())


if __name__ == "__main__":
    main()

