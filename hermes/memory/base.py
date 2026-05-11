from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class Memory(ABC):
    @abstractmethod
    def store(self, key: str, value: Any):
        pass

    @abstractmethod
    def retrieve(self, query: str, limit: int = 5) -> List[Any]:
        pass

class WorkingMemory(Memory):
    """
    Context (工作記憶): 儲存當前任務的短期資訊、變數與中間結果。
    """
    def __init__(self):
        self.buffer: List[Dict[str, Any]] = []

    def store(self, key: str, value: Any):
        self.buffer.append({
            "key": key,
            "value": value,
            "timestamp": None # 可以加入時間戳
        })

    def retrieve(self, query: str, limit: int = 5) -> List[Any]:
        # 簡單的關鍵字匹配或回傳最後幾筆
        return self.buffer[-limit:]

    def clear(self):
        self.buffer = []

class PromptMemory(Memory):
    """
    Prompt Memory (長期規則): 儲存系統指令、CONVENTIONS.md 與不變的工程原則。
    """
    def __init__(self):
        self.rules: Dict[str, str] = {}

    def store(self, key: str, value: str):
        self.rules[key] = value

    def retrieve(self, query: str, limit: int = 1) -> List[str]:
        if query in self.rules:
            return [self.rules[query]]
        return list(self.rules.values())[:limit]
