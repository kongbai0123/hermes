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
            "JSON 格式：{\"plan\":\"...\",\"worker\":\"file|search|test|external|self_development|explain\","
            "\"tool\":\"list_files|read_file|search_text|run_command|proxy_fetch|open_browser|external_codex|external_chat|external_chat_loop|self_improve|none\","
            "\"args\":{\"path\":\"...\",\"keyword\":\"...\",\"command\":\"...\",\"url\":\"...\","
            "\"browser\":\"chrome\",\"topic\":\"...\",\"mode\":\"self_optimization_discussion\","
            "\"message\":\"...\",\"target\":\"chatgpt_web\",\"max_turns\":\"3\","
            "\"goal\":\"...\",\"scope\":\"simple_agent\"}}\n"
            "若使用者要看結構，用 list_files。若要讀檔，用 read_file。"
            "若要找關鍵字，用 search_text。若要跑測試或版本，用 run_command。"
            "若使用者明確要求網路 proxy 或抓取外部 URL，用 proxy_fetch，args 必須包含 url。"
            "proxy_fetch 仍會經過 Policy Gate 與 allowlist，不可承諾一定能執行。"
            "若使用者要求開啟 Chrome 或瀏覽器網址，用 open_browser，args 必須包含 url 與 browser。"
            "open_browser 只能開啟設定檔 allowlist 允許的公開網域。"
            "若使用者要求外部 Codex、Codex 代理、或 Codex 與 Hermes 討論自我優化，"
            "用 external_codex，args 必須包含 topic 與 mode。"
            "若使用者要求 Hermes 到網頁版 GPT/ChatGPT 下達訊息並讀回回答，"
            "用 external_chat，args 必須包含 message 與 target=chatgpt_web。"
            "若使用者要求與外部 model 多輪、來回、連續聊天，"
            "用 external_chat_loop，args 必須包含 message、target=chatgpt_web 與 max_turns。"
            "若使用者要求 Hermes 修改、優化、開發自己的程式，"
            "用 self_improve，args 必須包含 goal、scope=simple_agent 與 mode=proposal_only。"
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
        if any(word in text for word in ["gpt", "chatgpt", "網頁版"]) and any(
            word in text for word in ["下達", "送出", "傳送", "讀回", "回答", "訊息"]
        ):
            message = self._extract_external_chat_message(user_text)
            if any(word in text for word in ["來回", "多輪", "連續", "繼續", "聊天", "不中斷"]):
                return ManagerDecision(
                    "到網頁版 GPT 下達訊息，並維持多輪來回對話。",
                    "external",
                    "external_chat_loop",
                    {
                        "message": message,
                        "target": "chatgpt_web",
                        "max_turns": str(self._extract_max_turns(user_text)),
                    },
                )
            return ManagerDecision(
                "到網頁版 GPT 下達訊息並讀回回答。",
                "external",
                "external_chat",
                {"message": message, "target": "chatgpt_web"},
            )
        if "hermes" in text and "codex" not in text and any(
            word in text for word in ["修改", "優化", "開發", "自己", "自身", "自我"]
        ):
            return ManagerDecision(
                "建立 Hermes 自我開發提案，先檢查自身程式並產生 patch proposal。",
                "self_development",
                "self_improve",
                {
                    "goal": user_text,
                    "scope": "simple_agent",
                    "mode": "proposal_only",
                },
            )
        if "codex" in text and any(word in text for word in ["hermes", "優化", "評估", "討論", "代理", "執行"]):
            return ManagerDecision(
                "建立受治理的外部 Codex 自我優化討論請求。",
                "external",
                "external_codex",
                {
                    "topic": user_text,
                    "mode": "self_optimization_discussion",
                },
            )
        if any(word in text for word in ["hermes", "優化", "開發", "評估", "規劃", "設計"]):
            return ManagerDecision(
                "先產生代理工作規劃，不直接執行未 template 化命令。",
                "explain",
                "none",
                {},
            )
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

    def _extract_external_chat_message(self, user_text: str) -> str:
        quote_match = re.search(r"[「『\"]([^」』\"]+)[」』\"]", user_text)
        if quote_match:
            return quote_match.group(1).strip()

        markers = ["下達", "送出", "傳送"]
        for marker in markers:
            if marker in user_text:
                tail = user_text.split(marker, 1)[1]
                tail = re.split(r"(並|且|然後|之後|讀回|回答)", tail, maxsplit=1)[0]
                if tail.strip():
                    return tail.strip(" ：:，,。")

        upper_match = re.search(r"\b(?!GPT\b|CHATGPT\b)([A-Z][A-Z0-9 _-]{0,80})\b", user_text)
        if upper_match:
            return upper_match.group(1).strip()
        return user_text.strip()

    def _extract_max_turns(self, user_text: str) -> int:
        match = re.search(r"(\d+)\s*(輪|次|turns?)", user_text, flags=re.I)
        if not match:
            return 3
        return max(1, min(int(match.group(1)), 8))


class WorkerModel:
    def __init__(self, llm: OllamaClient) -> None:
        self.llm = llm

    def respond(self, user_text: str, decision: ManagerDecision, observation: Observation) -> str:
        prompt = (
            "你是 Worker Model。請根據 Manager 的計畫與工具 Observation，"
            "用繁體中文給出務實、簡潔、可執行的回覆。\n"
            "請包含：結果摘要、下一步建議。\n"
            "你不是一般雲端聊天模型，而是 Hermes 本機代理的回覆層。"
            "若 Observation 顯示工具已執行，必須回報工具結果，不可宣稱無法操作本機。"
        )
        content = (
            f"使用者任務：{user_text}\n"
            f"Manager plan：{decision.plan}\n"
            f"Worker：{decision.worker}\n"
            f"Tool observation：\n{observation.format()}"
        )
        try:
            answer = self.llm.chat(
                [{"role": "system", "content": prompt}, {"role": "user", "content": content}]
            )
            if self._looks_like_generic_local_refusal(answer):
                return self._observation_first_answer(decision, observation)
            return answer
        except Exception:
            return self._observation_first_answer(decision, observation)

    def _looks_like_generic_local_refusal(self, answer: str) -> bool:
        refusal_markers = [
            "無法直接操作",
            "無法操作您電腦",
            "運作在雲端",
            "只能透過文字介面",
            "無法在您的本地環境中執行",
        ]
        return any(marker in answer for marker in refusal_markers)

    def _observation_first_answer(self, decision: ManagerDecision, observation: Observation) -> str:
        if observation.ok:
            return (
                "結果摘要：\n"
                f"已執行工具 `{observation.tool}`。\n\n"
                f"Observation：\n{observation.format()}\n\n"
                "下一步建議：若要繼續代理操作，請提出下一個具體目標；"
                "Hermes 會依 Policy Gate、白名單與 allowlist 判斷是否能自主執行。"
            )
        return (
            "結果摘要：\n"
            f"工具 `{observation.tool}` 未完成。\n\n"
            f"Observation：\n{observation.format()}\n\n"
            f"下一步建議：目前停止於 `{decision.tool}` 的工具結果，"
            "請檢查 policy、allowlist 或白名單設定。"
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
