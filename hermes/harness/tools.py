from typing import Callable, Dict, List, Literal, Any, Optional
from dataclasses import dataclass
from hermes.core.types import ToolResult

@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str
    permission: Literal["read", "generate", "write_proposal", "write", "shell", "test"]
    handler: Callable

class ToolRegistry:
    def __init__(self, executor: Any = None):
        self.tools: Dict[str, ToolSpec] = {}
        if executor:
            self._register_default_tools(executor)

    def _register_default_tools(self, executor):
        self.add_tool(ToolSpec(
            name="read_file",
            description="讀取檔案。參數: {'path': '路徑'}",
            permission="read",
            handler=executor.read_file
        ))
        self.add_tool(ToolSpec(
            name="list_files",
            description="列出目錄。參數: {'path': '路徑'}",
            permission="read",
            handler=executor.list_files
        ))
        self.add_tool(ToolSpec(
            name="grep_search",
            description="全域關鍵字搜尋。參數: {'query': '關鍵字', 'path': '路徑'}",
            permission="read",
            handler=executor.grep_search
        ))
        self.add_tool(ToolSpec(
            name="generate_design_artifact",
            description="生成設計/網站/應用/內容項目的安全草案，不寫入硬碟。參數: {'goal': '使用者想生成的項目', 'path': '參考工作區路徑'}",
            permission="generate",
            handler=executor.generate_design_artifact
        ))
        self.add_tool(ToolSpec(
            name="create_project_workspace",
            description="在 user_projects 底下建立隔離的使用者專案資料夾，並寫入 README.md 與 design_brief.md。參數: {'name': '專案資料夾名稱', 'brief': '需求描述'}",
            permission="write",
            handler=executor.create_project_workspace
        ))
        self.add_tool(ToolSpec(
            name="generate_static_site",
            description="在 user_projects 底下建立可直接開啟的靜態網站，寫入 index.html、styles.css、README.md 與 design_brief.md。參數: {'name': '專案資料夾名稱', 'brief': '網站需求描述'}",
            permission="write",
            handler=executor.generate_static_site
        ))
        self.add_tool(ToolSpec(
            name="propose_patch",
            description="提出變更建議 (不寫入硬碟，禁止 delete)。參數: {'task': '任務描述', 'changes': [{'path': '路徑', 'operation': 'modify/create', 'replacement': '新內容'}]}",
            permission="write_proposal",
            handler=executor.propose_patch
        ))
        self.add_tool(ToolSpec(
            name="apply_approved_patch",
            description="套用已授權的變更 (實體寫入)。參數: {'patch_id': 'ID', 'approval_token': 'Token'}",
            permission="write",
            handler=executor.apply_approved_patch
        ))
        self.add_tool(ToolSpec(
            name="run_tests",
            description="執行單元測試。參數: {'path': '測試目錄'}",
            permission="test",
            handler=executor.run_tests
        ))
        self.add_tool(ToolSpec(
            name="propose_shell_command",
            description="提出受治理 shell 指令建議，不直接執行。參數: {'command': '命令', 'reason': '原因', 'cwd': '工作目錄'}",
            permission="write_proposal",
            handler=executor.propose_shell_command
        ))
        self.add_tool(ToolSpec(
            name="execute_approved_shell",
            description="執行已批准的受治理 shell 指令。參數: {'proposal_id': 'ID', 'approval_token': 'Token'}",
            permission="shell",
            handler=executor.execute_approved_shell
        ))

    def add_tool(self, spec: ToolSpec):
        self.tools[spec.name] = spec

    def get_tool(self, name: str) -> Optional[ToolSpec]:
        return self.tools.get(name)

    def get_all_descriptions(self) -> str:
        return "\n".join([f"- {s.name}: {s.description}" for s in self.tools.values()])
