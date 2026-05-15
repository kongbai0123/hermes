import json
import urllib.request
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class LLMProvider(ABC):
    @abstractmethod
    def completion(self, prompt: str, system_prompt: Optional[str] = None) -> Dict[str, Any]:
        pass

class OllamaProvider(LLMProvider):
    def __init__(self, model: str = "llama3", base_url: str = "http://localhost:11434", temperature: float = 0.7, timeout: int = 180):
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.temperature = temperature
        self.timeout = timeout

    def completion(self, prompt: str, system_prompt: Optional[str] = None) -> Dict[str, Any]:
        url = f"{self.base_url}/api/chat"
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": self.temperature
            }
        }
        
        try:
            req = urllib.request.Request(
                url, 
                data=json.dumps(payload).encode('utf-8'),
                headers={'Content-Type': 'application/json'},
                method='POST'
            )
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                result = json.loads(response.read().decode('utf-8'))
                
            return {
                "text": result.get("message", {}).get("content", ""),
                "usage": {
                    "input": result.get("prompt_eval_count", 0),
                    "output": result.get("eval_count", 0),
                    "total": result.get("prompt_eval_count", 0) + result.get("eval_count", 0)
                },
                "raw": result
            }
        except Exception as e:
            raise Exception(f"Ollama API Error: {str(e)}")

class ClaudeProvider(LLMProvider):
    def completion(self, prompt: str, system_prompt: Optional[str] = None) -> Dict[str, Any]:
        pass

class MockLLMProvider(LLMProvider):
    def completion(self, prompt: str, system_prompt: Optional[str] = None) -> Dict[str, Any]:
        return {
            "text": f"[MOCK_FLOW_ONLY] 這是流程測試回覆，不是真實模型回答。原始指令：{prompt}",
            "usage": {"input": 10, "output": 20, "total": 30},
            "raw": {}
        }

def create_llm_provider(
    provider: str = "mock",
    model: Optional[str] = None,
    base_url: str = "http://localhost:11434",
    temperature: float = 0.7
) -> LLMProvider:
    provider_key = (provider or "mock").lower()

    if provider_key == "mock":
        return MockLLMProvider()

    if provider_key in {"ollama", "llama3", "llama"}:
        return OllamaProvider(
            model=model or ("llama3" if provider_key in {"ollama", "llama"} else provider),
            base_url=base_url,
            temperature=temperature
        )

    return OllamaProvider(
        model=model or provider,
        base_url=base_url,
        temperature=temperature
    )
