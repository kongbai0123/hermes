from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional

class Skill(ABC):
    """
    Skill (程序化記憶): 定義一個可重複執行的原子化能力。
    """
    def __init__(self, name: str, description: str, parameters: Dict[str, Any]):
        self.name = name
        self.description = description
        self.parameters = parameters # 定義輸入參數格式

    @abstractmethod
    def execute(self, **kwargs) -> Any:
        pass

class SkillRegistry:
    """
    技能倉庫: 儲存與管理所有已固化的 Skills。
    """
    def __init__(self):
        self.skills: Dict[str, Skill] = {}

    def register(self, skill: Skill):
        self.skills[skill.name] = skill
        print(f"[Skill] Registered: {skill.name}")

    def get_skill(self, name: str) -> Optional[Skill]:
        return self.skills.get(name)

    def list_skills(self) -> List[Dict[str, str]]:
        return [{"name": s.name, "description": s.description} for s in self.skills.values()]
