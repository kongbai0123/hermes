import json
import os
from typing import List, Dict, Any
from hermes.memory.base import Memory
from hermes.utils.paths import optimization_file

class SemanticMemory(Memory):
    """
    Session Search (情節記憶) & RAG: 儲存歷史對話與結構化知識。
    目前以本地 JSON 模擬向量檢索，未來可升級為 ChromaDB/FAISS。
    """
    def __init__(self, storage_path: str | None = None):
        self.storage_path = storage_path or optimization_file("memory_semantic.json")
        self.data: List[Dict[str, Any]] = []
        self._load()

    def _load(self):
        if os.path.exists(self.storage_path):
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                self.data = json.load(f)

    def _save(self):
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
        with open(self.storage_path, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=4, ensure_ascii=False)

    def store(self, content: str, metadata: Dict[str, Any] = None):
        self.data.append({
            "content": content,
            "metadata": metadata or {},
            "id": len(self.data)
        })
        self._save()

    def retrieve(self, query: str, limit: int = 3) -> List[Dict[str, Any]]:
        # 簡單的關鍵字搜尋模擬語義檢索
        results = []
        query_words = query.lower().split()
        
        for item in self.data:
            score = sum(1 for word in query_words if word in item["content"].lower())
            if score > 0:
                results.append((score, item))
        
        # 按匹配分數排序
        results.sort(key=lambda x: x[0], reverse=True)
        return [item for score, item in results[:limit]]

class UserModeling(Memory):
    """
    User Modeling (個性模型): 儲存用戶偏好、風格與習慣。
    """
    def __init__(self, storage_path: str | None = None):
        self.storage_path = storage_path or optimization_file("user_model.json")
        self.preferences: Dict[str, Any] = {}
        self._load()

    def _load(self):
        if os.path.exists(self.storage_path):
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                self.preferences = json.load(f)

    def _save(self):
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
        with open(self.storage_path, 'w', encoding='utf-8') as f:
            json.dump(self.preferences, f, indent=4, ensure_ascii=False)

    def store(self, key: str, value: Any):
        self.preferences[key] = value
        self._save()

    def retrieve(self, query: str, limit: int = 1) -> List[Any]:
        if query in self.preferences:
            return [self.preferences[query]]
        return [self.preferences] # 回傳完整模型
