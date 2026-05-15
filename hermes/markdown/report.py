from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class MarkdownHeading:
    level: int
    text: str
    line: int


def extract_markdown_toc(content: str) -> list[dict]:
    headings: list[dict] = []
    for line_number, line in enumerate((content or "").splitlines(), start=1):
        match = re.match(r"^(#{1,6})\s+(.+)$", line)
        if not match:
            continue
        text = re.sub(r"[#*_`]", "", match.group(2)).strip()
        headings.append({"level": len(match.group(1)), "text": text, "line": line_number})
    return headings


def summarize_markdown_report(content: str, max_chars: int = 700) -> dict:
    toc = extract_markdown_toc(content)
    title = toc[0]["text"] if toc else "Markdown report"
    body_lines = [
        line.strip()
        for line in (content or "").splitlines()
        if line.strip() and not line.lstrip().startswith("#") and not line.strip() == "---"
    ]
    summary_text = " ".join(body_lines)[:max_chars]
    return {
        "title": title,
        "summary": summary_text,
        "toc": toc,
        "sections": len(toc),
    }
