import json
import re
from typing import Optional, Dict, Any
from hermes.core.types import ToolPlan

class ToolPlanner:
    """
    工具計畫解析器: 負責將模型的自然語言輸出轉換為結構化的 ToolPlan。
    """
    def __init__(self, registry: Any):
        self.registry = registry

    def parse_output(self, llm_output: str) -> Optional[ToolPlan]:
        # 1. JSON 擷取
        json_obj = self._extract_json(llm_output)
        if json_obj:
            tool = json_obj.get("tool")
            args = json_obj.get("args", {})
            # 統一參數為 path
            path = args.get("path") or args.get("file_path") or args.get("directory")
            
            if tool and path and self.registry.get_tool(tool):
                return ToolPlan(tool=tool, args={"path": path}, reason=json_obj.get("reason", ""))

        # 2. 啟發式解析 (Heuristic Fallback)
        return self._heuristic_fallback(llm_output)

    def _extract_json(self, text: str) -> Optional[Dict[str, Any]]:
        try:
            match = re.search(r'(\{.*\})', text, re.DOTALL)
            if match:
                return json.loads(match.group(1))
        except: pass
        return None

    def _heuristic_fallback(self, text: str) -> Optional[ToolPlan]:
        t = text.lower()
        # 偵測檔案路徑
        m = re.search(r'([a-zA-Z0-9_\-\./]+\.(py|md|txt|json|yaml|yml|html|css|js|ts|toml))', text)
        if m and any(k in t for k in ["讀", "看", "read", "view", "cat"]):
            return ToolPlan(tool="read_file", args={"path": m.group(1)}, reason="Heuristic: read intent")
        
        # 偵測目錄列表
        if any(k in t for k in ["列出", "目錄", "ls", "list", "dir"]):
            return ToolPlan(tool="list_files", args={"path": "."}, reason="Heuristic: list intent")
            
        return None
