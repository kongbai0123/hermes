from hermes.skills.base import Skill, SkillRegistry
from typing import Dict, Any, List

class FileSystemSkill(Skill):
    """
    範例技能：檔案系統操作
    """
    def __init__(self):
        super().__init__(
            name="file_organizer",
            description="Organizes files in a directory based on their extensions.",
            parameters={"path": "string", "rules": "dict"}
        )

    def execute(self, **kwargs) -> str:
        path = kwargs.get("path")
        return f"Successfully organized files in {path} using rules."

class SkillCompiler:
    """
    技能編譯器: 將執行軌跡 (Trace) 轉化為可重用的 Skill。
    """
    def __init__(self, registry: SkillRegistry):
        self.registry = registry

    def compile_from_trace(self, trace_data: Dict[str, Any]) -> str:
        """
        模擬從執行紀錄中提取技能並包裝的過程。
        """
        # 這裡未來會用 LLM 分析 trace_data，自動生成參數化腳本
        skill_name = f"auto_skill_{len(self.registry.skills)}"
        
        # 建立一個虛擬技能
        class DynamicSkill(Skill):
            def execute(self, **kwargs):
                return f"Executing compiled skill: {skill_name}"
        
        new_skill = DynamicSkill(
            name=skill_name,
            description=f"Auto-compiled skill from task: {trace_data.get('task')}",
            parameters={}
        )
        
        self.registry.register(new_skill)
        return skill_name
