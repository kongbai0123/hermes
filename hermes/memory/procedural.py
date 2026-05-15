import json
import os
from typing import List, Dict, Any, Optional
from hermes.memory.base import Memory
from hermes.utils.paths import optimization_file

class ProceduralMemory(Memory):
    """
    Process Memory (技能記憶): 儲存已固化的技能定義與其執行範例。
    這讓 Agent 知道「如何」執行特定複雜任務。
    """
    def __init__(self, storage_path: str | None = None):
        self.storage_path = storage_path or optimization_file("memory_procedural.json")
        self.skills_data: Dict[str, Any] = {}
        self._load()

    def _load(self):
        if os.path.exists(self.storage_path):
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                self.skills_data = json.load(f)

    def _save(self):
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
        with open(self.storage_path, 'w', encoding='utf-8') as f:
            json.dump(self.skills_data, f, indent=4, ensure_ascii=False)

    def store(self, skill_name: str, definition: Dict[str, Any]):
        self.skills_data[skill_name] = definition
        self._save()

    def retrieve(self, query: str, limit: int = 3) -> List[Dict[str, Any]]:
        # 根據描述搜尋適合的技能
        results = []
        query_words = query.lower().split()
        
        for name, data in self.skills_data.items():
            desc = data.get("description", "").lower()
            score = sum(1 for word in query_words if word in desc or word in name.lower())
            if score > 0:
                results.append((score, data))
        
        results.sort(key=lambda x: x[0], reverse=True)
        return [data for score, data in results[:limit]]
