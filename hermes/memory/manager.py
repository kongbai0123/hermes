from hermes.memory.base import WorkingMemory, PromptMemory
from hermes.memory.long_term import SemanticMemory, UserModeling
from hermes.memory.procedural import ProceduralMemory
from typing import Dict, Any, List

class MemoryManager:
    def __init__(self):
        self.working = WorkingMemory()
        self.prompt = PromptMemory()
        self.semantic = SemanticMemory()
        self.user = UserModeling()
        self.procedural = ProceduralMemory()
        
        # 初始化預設規則
        self._init_defaults()

    def _init_defaults(self):
        self.prompt.store("system_identity", "You are Hermes Agent OS, an evolving execution system.")
        self.prompt.store("engineering_principles", "SRP, SoC, Layered Architecture, Observability.")

    def get_context(self, query: str) -> Dict[str, Any]:
        """
        同時從多個記憶層提取相關資訊，構建任務上下文。
        """
        return {
            "working": self.working.retrieve(query),
            "user_prefs": self.user.retrieve("general"),
            "relevant_knowledge": self.semantic.retrieve(query),
            "available_skills": self.procedural.retrieve(query),
            "system_rules": self.prompt.retrieve("system_identity")
        }

    def consolidate_session(self, task: str, result: str):
        """
        將任務與結果存入情節記憶 (Session Search)。
        """
        self.semantic.store(
            content=f"Task: {task}\nResult: {result}",
            metadata={"type": "session_summary"}
        )
