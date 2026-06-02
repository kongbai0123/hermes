"""Part 3-1: prompt design for local agents."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

from agent.llm import generate


QUESTION = "請找出 Python 函式 divide(a, b) 可能需要注意的錯誤。"


def main() -> None:
    loose_prompt = QUESTION
    structured_prompt = f"""
你是程式碼審查助理。請用以下格式回答：
1. 風險
2. 為什麼會發生
3. 建議測試
4. 建議修正

問題：{QUESTION}
"""

    print("=== 鬆散 Prompt ===")
    print(generate(loose_prompt, temperature=0.2))
    print("\n=== 結構化 Prompt ===")
    print(generate(structured_prompt, temperature=0.2))


if __name__ == "__main__":
    main()

