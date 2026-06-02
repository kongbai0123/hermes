"""Part 3-3: review a patch before applying it."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

from agent.tools import propose_patch


PATCH = """--- a/sample_project/calculator.py
+++ b/sample_project/calculator.py
@@
 def divide(a, b):
-    # Intentional bug for lesson 7: this should reject division by zero clearly.
+    if b == 0:
+        raise ValueError("division by zero")
     return a / b
@@
 def average(numbers):
+    if not numbers:
+        raise ValueError("numbers cannot be empty")
     return sum(numbers) / len(numbers)
"""


def main() -> None:
    print("Agent 產生的 patch 應該先審查，不要直接套用。\n")
    print("審查重點：")
    print("1. 是否只改預期檔案")
    print("2. 是否處理真正錯誤")
    print("3. 是否新增不必要行為")
    print("4. 是否需要補測試\n")
    print(propose_patch({"path": "sample_project/calculator.py", "patch": PATCH}).to_observation())


if __name__ == "__main__":
    main()

