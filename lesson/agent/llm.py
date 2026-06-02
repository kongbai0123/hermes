"""Small Ollama client used by the lessons and the agent."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Iterable


DEFAULT_MODEL = "gemma4:latest"
OLLAMA_URL = "http://localhost:11434/api/generate"


class OllamaError(RuntimeError):
    """Raised when the local Ollama API cannot complete a request."""


def generate(
    prompt: str,
    *,
    model: str = DEFAULT_MODEL,
    system: str | None = None,
    temperature: float = 0.2,
    stream: bool = False,
) -> str | Iterable[str]:
    """Generate text from Ollama.

    When stream is False, returns one string. When stream is True, returns an
    iterator of response chunks.
    """

    payload = {
        "model": model,
        "prompt": prompt,
        "stream": stream,
        "options": {"temperature": temperature},
    }
    if system:
        payload["system"] = system

    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        OLLAMA_URL,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    if stream:
        return _stream_response(request)
    return _single_response(request)


def _single_response(request: urllib.request.Request) -> str:
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            body = json.loads(response.read().decode("utf-8"))
            return str(body.get("response", ""))
    except urllib.error.URLError as exc:
        raise OllamaError(f"Cannot reach Ollama at {OLLAMA_URL}: {exc}") from exc


def _stream_response(request: urllib.request.Request) -> Iterable[str]:
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            for raw_line in response:
                if not raw_line:
                    continue
                line = json.loads(raw_line.decode("utf-8"))
                chunk = line.get("response", "")
                if chunk:
                    yield str(chunk)
    except urllib.error.URLError as exc:
        raise OllamaError(f"Cannot reach Ollama at {OLLAMA_URL}: {exc}") from exc

