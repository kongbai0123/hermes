# hermes/core/tool_planner.py
import json
import re
from typing import Optional, Dict, Any
from hermes.core.types import ToolPlan

class ToolPlanner:
    def __init__(self, registry: Any):
        self.registry = registry

    def parse_output(self, llm_output: str) -> Optional[ToolPlan]:
        json_obj = self._extract_json(llm_output)
        if json_obj:
            tool = json_obj.get("tool")
            args = json_obj.get("args", {})
            path = args.get("path") or args.get("file_path") or args.get("directory")
            if tool and path and self.registry.get_tool(tool):
                return ToolPlan(tool=tool, args={"path": path}, reason=json_obj.get("reason", ""))
        return self._heuristic_fallback(llm_output)

    def _extract_json(self, text: str) -> Optional[Dict[str, Any]]:
        try:
            match = re.search(r'(\{.*\})', text, re.DOTALL)
            return json.loads(match.group(1)) if match else None
        except: return None

    def _heuristic_fallback(self, text: str) -> Optional[ToolPlan]:
        t = text.lower()
        m = re.search(r'([a-zA-Z0-9_\-\./]+\.(py|md|txt|json|yaml|yml|html|css|js|ts|toml))', text)
        if m and any(k in t for k in ["讀", "看", "read", "view", "cat"]):
            return ToolPlan(tool="read_file", args={"path": m.group(1)}, reason="Heuristic: read")
        if any(k in t for k in ["列出", "目錄", "ls", "list", "dir"]):
            return ToolPlan(tool="list_files", args={"path": "."}, reason="Heuristic: list")
        return None

# hermes/harness/tools.py (MODIFIED)
# ... descriptions updated to {'path': '...'}
