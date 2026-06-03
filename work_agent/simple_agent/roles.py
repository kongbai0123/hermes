from __future__ import annotations

import json
import re
from dataclasses import dataclass

from .llm import OllamaClient
from .tools import Observation, ToolBox


@dataclass
class ManagerDecision:
    plan: str
    worker: str
    tool: str
    args: dict[str, str]


class ManagerModel:
    def __init__(self, llm: OllamaClient) -> None:
        self.llm = llm

    def decide(self, user_text: str) -> ManagerDecision:
        prompt = (
            "你是 Manager Model。請把使用者任務轉成簡單決策。\n"
            "只能輸出 JSON，不要 markdown。\n"
            "JSON 格式：{\"plan\":\"...\",\"worker\":\"file|search|test|explain\","
            "\"tool\":\"list_files|read_file|search_text|run_command|proxy_fetch|open_browser|none\","
            "\"args\":{\"path\":\"...\",\"keyword\":\"...\",\"command\":\"...\",\"url\":\"...\",\"browser\":\"chrome\"}}\n"
            "若使用者要看結構，用 list_files。若要讀檔，用 read_file。"
            "若要找關鍵字，用 search_text。若要跑測試或版本，用 run_command。"
            "若使用者明確要求網路 proxy 或抓取外部 URL，用 proxy_fetch，args 必須包含 url。"
            "proxy_fetch 仍會經過 Policy Gate 與 allowlist，不可承諾一定能執行。"
            "若使用者要求開啟 Chrome 或瀏覽器網址，用 open_browser，args 必須包含 url 與 browser。"
            "open_browser 只能開啟設定檔 allowlist 允許的公開網域。"
        )
        try:
            raw = self.llm.chat(
                [{"role": "system", "content": prompt}, {"role": "user", "content": user_text}]
            )
            data = self._extract_json(raw)
            return ManagerDecision(
                plan=str(data.get("plan", "依任務選擇工具並整理結果。")),
                worker=str(data.get("worker", "explain")),
                tool=str(data.get("tool", "none")),
                args={str(k): str(v) for k, v in dict(data.get("args", {})).items()},
            )
        except Exception:
            return self._fallback_decision(user_text)

    def _extract_json(self, raw: str) -> dict:
        match = re.search(r"\{.*\}", raw, flags=re.S)
        if not match:
            raise ValueError("模型沒有輸出 JSON")
        return json.loads(match.group(0))

    def _fallback_decision(self, user_text: str) -> ManagerDecision:
        text = user_text.lower()
        if any(word in text for word in ["搜尋", "search", "找出", "關鍵字"]):
            keyword = user_text.split()[-1] if user_text.split() else ""
            return ManagerDecision("搜尋 workspace 內的關鍵字。", "search", "search_text", {"keyword": keyword})
        if any(word in text for word in ["讀取", "read", "打開", "查看檔案"]):
            path = user_text.split()[-1] if user_text.split() else "."
            return ManagerDecision("讀取指定檔案。", "file", "read_file", {"path": path})
        if any(word in text for word in ["測試", "pytest", "執行", "version"]):
            command = "python --version" if "version" in text else "pytest"
            return ManagerDecision("執行白名單命令。", "test", "run_command", {"command": command})
        if any(word in text for word in ["chrome", "browser", "瀏覽器", "youtube", "開啟網頁", "打開網頁"]):
            url_match = re.search(r"https?://\S+", user_text)
            url = url_match.group(0).rstrip("。.,，") if url_match else ""
            if not url and "youtube" in text:
                url = "https://www.youtube.com"
            return ManagerDecision(
                "使用 open_browser 讓 Chrome 開啟使用者指定的公開網頁。",
                "browser",
                "open_browser",
                {"url": url, "browser": "chrome"},
            )
        if any(word in text for word in ["代理", "proxy", "api", "網路請求", "爬取", "抓取"]):
            url_match = re.search(r"https?://\S+", user_text)
            url = url_match.group(0).rstrip("。.,，") if url_match else ""
            return ManagerDecision(
                "使用 proxy_fetch 嘗試抓取外部 URL，但必須先通過 Policy Gate、approval 與 domain allowlist。",
                "network",
                "proxy_fetch",
                {"url": url},
            )
        if any(word in text for word in ["browser", "瀏覽器"]):
            return ManagerDecision("目前版本尚未接上 Browser 操作工具。", "explain", "none", {})
        return ManagerDecision("列出 workspace 結構後整理說明。", "file", "list_files", {"path": "."})


class WorkerModel:
    def __init__(self, llm: OllamaClient) -> None:
        self.llm = llm

    def respond(self, user_text: str, decision: ManagerDecision, observation: Observation) -> str:
        prompt = (
            "你是 Worker Model。請根據 Manager 的計畫與工具 Observation，"
            "用繁體中文給出務實、簡潔、可執行的回覆。\n"
            "請包含：結果摘要、下一步建議。"
        )
        content = (
            f"使用者任務：{user_text}\n"
            f"Manager plan：{decision.plan}\n"
            f"Worker：{decision.worker}\n"
            f"Tool observation：\n{observation.format()}"
        )
        try:
            return self.llm.chat(
                [{"role": "system", "content": prompt}, {"role": "user", "content": content}]
            )
        except Exception:
            return (
                f"結果摘要：\n{observation.format()}\n\n"
                "下一步建議：確認工具結果是否符合你的任務，再指定要讀取、搜尋或執行的項目。"
            )


class ExplainWorker:
    def __init__(self, llm: OllamaClient) -> None:
        self.llm = llm

    def explain_architecture(self) -> str:
        return (
            "Hermes Bounded Closed Loop：\n"
            "- Loop Controller：負責步數、重試、停止原因、trace 與 hard limits。\n"
            "- Planner Agent：由 Manager Model 擔任，負責拆任務、選工具與提出計畫。\n"
            "- Processor Agent：由 Worker Model 擔任，負責整理 observation 與輸出可讀回覆。\n"
            "- Policy Gate：負責 allow / deny / approval_required，不可被模型覆蓋。\n"
            "- Executor：只執行註冊工具，不做任務推理。\n"
            "- Energy Monitor：提供 continue / replan / stop / ask_user 的啟發式風險訊號。"
        )
