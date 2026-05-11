from typing import Callable, Dict, List, Literal, Any, Optional
from dataclasses import dataclass
from hermes.core.types import ToolResult

@dataclass(frozen=True)
class ToolSpec:
    """定義工具的規格與權限"""
    name: str
    description: str
    permission: Literal["read", "write", "shell", "network"]
    handler: Callable

class ToolRegistry:
    """Hermes 工具註冊中心"""
    def __init__(self, executor: Any = None):
        self.tools: Dict[str, ToolSpec] = {}
        if executor:
            self._register_default_tools(executor)

    def _register_default_tools(self, executor):
        # 註冊唯讀工具
        self.add_tool(ToolSpec(
            name="read_file",
            description="讀取指定檔案的內容。參數: {'file_path': '路徑'}",
            permission="read",
            handler=executor.read_file
        ))
        
        self.add_tool(ToolSpec(
            name="list_files",
            description="列出目錄下的檔案清單。參數: {'directory': '路徑'}",
            permission="read",
            handler=executor.list_files
        ))

    def add_tool(self, spec: ToolSpec):
        self.tools[spec.name] = spec

    def get_tool(self, name: str) -> Optional[ToolSpec]:
        return self.tools.get(name)

    def get_all_descriptions(self) -> str:
        """格式化所有工具描述，供模型 Prompt 使用"""
        lines = []
        for name, spec in self.tools.items():
            lines.append(f"- {name}: {spec.description}")
        return "\n".join(lines)
