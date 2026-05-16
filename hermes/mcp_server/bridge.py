import json
import os
import socket
import urllib.error
import urllib.request


class HermesAPIBridge:
    def __init__(self, base_url: str | None = None, timeout_seconds: float = 5.0):
        self.base_url = (base_url or os.getenv("HERMES_BASE_URL") or "http://localhost:8000").rstrip("/")
        self.timeout_seconds = float(os.getenv("HERMES_API_TIMEOUT_SECONDS", str(timeout_seconds)))

    def run_task(
        self,
        task: str,
        provider: str | None = None,
        model: str | None = None,
        base_url: str | None = None,
        temperature: float | None = None,
    ) -> tuple[dict, bool]:
        # 決定 Provider
        resolved_provider = (
            provider or 
            os.getenv("HERMES_MCP_PROVIDER") or 
            os.getenv("HERMES_DEFAULT_PROVIDER") or 
            "mock"
        )
        
        # 決定來源標記
        provider_source = "default"
        if provider: provider_source = "argument"
        elif os.getenv("HERMES_MCP_PROVIDER"): provider_source = "env"
        elif os.getenv("HERMES_DEFAULT_PROVIDER"): provider_source = "env_default"

        payload = {
            "task": task,
            "provider": resolved_provider,
            "metadata": {
                "source": "mcp",
                "client": "claude_code",
                "entrypoint": "hermes.mcp_server",
                "tool": "hermes.run_task",
                "provider_source": provider_source
            },
        }

        # 決定 Model
        resolved_model = (
            model or 
            os.getenv("HERMES_MCP_MODEL") or 
            os.getenv("HERMES_DEFAULT_MODEL")
        )
        if resolved_model:
            payload["model"] = resolved_model

        # 決定 Base URL
        resolved_base_url = (
            base_url or 
            os.getenv("HERMES_MCP_BASE_URL") or 
            os.getenv("HERMES_OLLAMA_BASE_URL")
        )
        if resolved_base_url:
            payload["base_url"] = resolved_base_url

        # 決定 Temperature
        resolved_temp = (
            temperature if temperature is not None else 
            os.getenv("HERMES_MCP_TEMPERATURE")
        )
        if resolved_temp is not None:
            try:
                payload["temperature"] = float(resolved_temp)
            except (ValueError, TypeError):
                pass

        return self._request_json("POST", "/api/task", payload)

    def get_status(self) -> tuple[dict, bool]:
        return self._request_json("GET", "/api/status")

    def get_trace(self) -> tuple[dict | list, bool]:
        return self._request_json("GET", "/api/logs")

    def _request_json(self, method: str, path: str, payload: dict | None = None) -> tuple[dict | list, bool]:
        request_body = None
        headers = {}
        if payload is not None:
            request_body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            headers["Content-Type"] = "application/json"
            headers["X-Hermes-Source"] = "mcp"
            headers["X-Hermes-Client"] = "claude_code"
        request = urllib.request.Request(f"{self.base_url}{path}", data=request_body, method=method, headers=headers)

        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                raw = response.read().decode("utf-8")
                try:
                    return json.loads(raw), False
                except json.JSONDecodeError as exc:
                    return self._error_payload("INVALID_JSON_RESPONSE", f"Hermes API returned invalid JSON: {exc}"), True
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            return self._error_payload("HTTP_ERROR", f"Hermes API returned HTTP {exc.code}", status=exc.code, detail=detail), True
        except (urllib.error.URLError, ConnectionError, socket.timeout, TimeoutError) as exc:
            return self._error_payload("HERMES_API_UNAVAILABLE", "Hermes API unavailable", detail=str(exc), base_url=self.base_url), True

    def _error_payload(self, code: str, message: str, **extra) -> dict:
        payload = {"ok": False, "error": {"code": code, "message": message}}
        payload["error"].update({key: value for key, value in extra.items() if value is not None})
        return payload
