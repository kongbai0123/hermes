import json
import re
from typing import Optional, Dict, Any
from hermes.core.types import ToolPlan

class ToolPlanner:
    def __init__(self, registry: Any):
        self.registry = registry

    def parse_output(self, llm_output: str, allow_heuristic: bool = True) -> Optional[ToolPlan]:
        json_obj = self._extract_json(llm_output)
        if json_obj:
            tool = json_obj.get("tool")
            args = json_obj.get("args", {})
            
            if tool and self.registry.get_tool(tool):
                final_args = dict(args)
                if "file_path" in final_args and "path" not in final_args:
                    final_args["path"] = final_args.pop("file_path")
                if "directory" in final_args and "path" not in final_args:
                    final_args["path"] = final_args.pop("directory")
                if tool in {"read_file", "list_files", "grep_search", "run_tests", "generate_design_artifact"}:
                    final_args.setdefault("path", ".")
                return ToolPlan(tool=tool, args=final_args, reason=json_obj.get("reason", ""))

        if not allow_heuristic:
            return None
        return self._heuristic_fallback(llm_output)

    def _extract_json(self, text: str) -> Optional[Dict[str, Any]]:
        try:
            match = re.search(r'(\{.*\})', text, re.DOTALL)
            return json.loads(match.group(1)) if match else None
        except: return None

    def _heuristic_fallback(self, text: str) -> Optional[ToolPlan]:
        t = text.lower()
        
        # 1. 偵測搜尋意圖
        if any(k in t for k in ["搜尋", "grep", "search", "找"]):
            # 嘗試提取引號內的關鍵字
            query_match = re.search(r'["\']([^"\']+)["\']', text)
            query = query_match.group(1) if query_match else ""
            if query:
                return ToolPlan(tool="grep_search", args={"query": query, "path": "."}, reason="Heuristic: search intent")

        # 2. 偵測測試意圖
        if any(k in t for k in ["執行測試", "跑測試", "運行測試", "run_tests", "pytest", "unittest", "run tests"]):
            return ToolPlan(tool="run_tests", args={"path": "tests"}, reason="Heuristic: test intent")

        # 3. 偵測建立隔離專案工作區意圖
        wants_create_workspace = any(k in t for k in ["建立", "新增", "create", "mkdir", "資料夾", "folder", "專案", "project"])
        wants_generation = any(k in t for k in ["設計", "生成", "製作", "產生", "網站", "頁面", "app", "application"])
        if wants_create_workspace and wants_generation:
            return ToolPlan(
                tool="create_project_workspace",
                args={"name": "generated-project", "brief": text.strip()},
                reason="Heuristic: controlled project workspace creation intent"
            )

        # 4. 偵測設計/生成意圖
        if any(k in t for k in ["設計", "生成", "製作", "產生", "網站", "頁面", "app", "application"]):
            return ToolPlan(
                tool="generate_design_artifact",
                args={"goal": text.strip(), "path": "."},
                reason="Heuristic: design generation intent"
            )

        # 5. 偵測讀取意圖
        m = re.search(r'([a-zA-Z0-9_\-\./]+\.(py|md|txt|json|yaml|yml|html|css|js|ts|toml))', text)
        if m and any(k in t for k in ["讀", "看", "read", "view", "cat"]):
            return ToolPlan(tool="read_file", args={"path": m.group(1)}, reason="Heuristic: read intent")
        
        # 6. 偵測目錄列表
        if any(k in t for k in ["列出", "目錄", "ls", "list", "dir"]):
            return ToolPlan(tool="list_files", args={"path": "."}, reason="Heuristic: list intent")
            
        return None
