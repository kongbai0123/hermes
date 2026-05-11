import json
import re
from typing import Optional, Dict, Any
from hermes.core.types import ToolPlan
from hermes.harness.tools import ToolRegistry

class ToolPlanner:
    """
    工具計畫解析器: 負責將模型的自然語言輸出轉換為結構化的 ToolPlan。
    """
    def __init__(self, registry: ToolRegistry):
        self.registry = registry

    def parse_output(self, llm_output: str) -> Optional[ToolPlan]:
        # 1. 嘗試提取 JSON
        json_obj = self._extract_json(llm_output)
        if json_obj:
            # 統一參數轉化: 如果模型給了 file_path 或 directory，統一轉為 path
            tool = json_obj.get("tool")
            args = json_obj.get("args", {})
            path = args.get("path") or args.get("file_path") or args.get("directory")
            
            if tool and path:
                return ToolPlan(tool=tool, args={"path": path}, reason=json_obj.get("reason", ""))

        # 2. Heuristic Fallback
        return self._heuristic_fallback(llm_output)

    def _extract_json(self, text: str) -> Optional[Dict[str, Any]]:
        try:
            match = re.search(r'(\{.*\})', text, re.DOTALL)
            if match:
                return json.loads(match.group(1))
        except:
            pass
        return None

    def _heuristic_fallback(self, text: str) -> Optional[ToolPlan]:
        text_lower = text.lower()
        
        # 偵測路徑
        path_match = re.search(r'([a-zA-Z0-9_\-\./]+\.(py|md|txt|json|yaml|yml|html|css|js|ts|toml))', text)
        
        if path_match:
            path = path_match.group(1)
            if any(k in text_lower for k in ["讀取", "讀", "看", "read", "view", "cat", "open"]):
                return ToolPlan(tool="read_file", args={"path": path}, reason="Heuristic: read intent")
        
        if any(k in text_lower for k in ["列出", "目錄", "ls", "list", "dir"]):
            dir_match = re.search(r'(目錄|dir|in)\s*([a-zA-Z0-9_\-\./]+)', text_lower)
            target_dir = dir_match.group(2) if dir_match else "."
            return ToolPlan(tool="list_files", args={"path": target_dir}, reason="Heuristic: list intent")
            
        return None
