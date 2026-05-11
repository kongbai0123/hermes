from typing import Callable, Dict, List, Literal, Any, Optional
from dataclasses import dataclass
from hermes.core.types import ToolResult

@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str
    permission: Literal["read", "write", "shell", "network"]
    handler: Callable

class ToolRegistry:
    def __init__(self, executor: Any = None):
        self.tools: Dict[str, ToolSpec] = {}
        if executor:
            self._register_default_tools(executor)

    def _register_default_tools(self, executor):
        self.add_tool(ToolSpec(
            name="read_file",
            description="讀取指定路徑的檔案內容。參數: {'path': '檔案路徑'}",
            permission="read",
            handler=executor.read_file
        ))
        self.add_tool(ToolSpec(
            name="list_files",
            description="列出指定目錄下的檔案清單。參數: {'path': '目錄路徑'}",
            permission="read",
            handler=executor.list_files
        ))

    def add_tool(self, spec: ToolSpec):
        self.tools[spec.name] = spec

    def get_tool(self, name: str) -> Optional[ToolSpec]:
        return self.tools.get(name)

    def get_all_descriptions(self) -> str:
        return "\n".join([f"- {s.name}: {s.description}" for s in self.tools.values()])
