from typing import Callable, Dict, List, Literal, Any, Optional
from dataclasses import dataclass
from hermes.core.types import ToolResult

@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str
    permission: Literal["read", "write", "shell", "network", "test"]
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
            description="全域關鍵字搜尋。參數: {'query': '關鍵字', 'path': '搜尋起點'}",
            permission="read",
            handler=executor.grep_search
        ))
        self.add_tool(ToolSpec(
            name="run_tests",
            description="執行單元測試。參數: {'path': '測試目錄'}",
            permission="test",
            handler=executor.run_tests
        ))

    def add_tool(self, spec: ToolSpec):
        self.tools[spec.name] = spec

    def get_tool(self, name: str) -> Optional[ToolSpec]:
        return self.tools.get(name)

    def get_all_descriptions(self) -> str:
        return "\n".join([f"- {s.name}: {s.description}" for s in self.tools.values()])
