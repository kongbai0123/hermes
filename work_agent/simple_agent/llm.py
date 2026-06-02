from __future__ import annotations

import json
import urllib.error
import urllib.request


class OllamaClient:
    def __init__(self, model: str, url: str) -> None:
        self.model = model
        self.url = url

    def chat(self, messages: list[dict[str, str]], temperature: float = 0.2) -> str:
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {"temperature": temperature},
        }
        data = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            self.url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                result = json.loads(response.read().decode("utf-8"))
        except urllib.error.URLError as exc:
            raise RuntimeError(
                "無法連線到 Ollama。請先確認 Ollama 已啟動，且模型已安裝。"
            ) from exc
        return result.get("message", {}).get("content", "").strip()

