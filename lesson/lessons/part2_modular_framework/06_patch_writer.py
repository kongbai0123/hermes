"""Lesson 6: produce a patch proposal without applying it."""

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
"""


def main() -> None:
    result = propose_patch({"path": "sample_project/calculator.py", "patch": PATCH})
    print(result.to_observation())


if __name__ == "__main__":
    main()

