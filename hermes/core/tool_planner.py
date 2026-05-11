import json
import re
from typing import Optional, Dict, Any, Tuple
from hermes.core.types import ToolPlan
from hermes.harness.tools import ToolRegistry

class ToolPlanner:
    """
    工具計畫解析器: 負責將模型的自然語言輸出轉換為結構化的 ToolPlan。
    具備 JSON 提取與啟發式 Fallback 機制。
    """
    def __init__(self, registry: ToolRegistry):
        self.registry = registry

    def parse_output(self, llm_output: str) -> Optional[ToolPlan]:
        """解析模型輸出並生成工具計畫"""
        # 1. 嘗試提取 JSON
        json_obj = self._extract_json(llm_output)
        if json_obj:
            plan = self._create_plan_from_json(json_obj)
            if plan: return plan

        # 2. 如果 JSON 失敗，執行啟發式偵測 (Heuristic Fallback)
        return self._heuristic_fallback(llm_output)

    def _extract_json(self, text: str) -> Optional[Dict[str, Any]]:
        """從文本中抓取第一個合法的 JSON 物件"""
        try:
            # 尋找最外層的 { ... }
            match = re.search(r'(\{.*\})', text, re.DOTALL)
            if match:
                return json.loads(match.group(1))
        except:
            pass
        return None

    def _create_plan_from_json(self, data: Dict[str, Any]) -> Optional[ToolPlan]:
        """從 JSON 數據建立並驗證計畫"""
        tool_name = data.get("tool")
        args = data.get("args", {})
        
        # 驗證工具是否存在
        if tool_name and self.registry.get_tool(tool_name):
            return ToolPlan(
                tool=tool_name,
                args=args,
                reason=data.get("reason", "LLM JSON output")
            )
        return None

    def _heuristic_fallback(self, text: str) -> Optional[ToolPlan]:
        """
        啟發式 Fallback：當 JSON 解析失敗時，偵測關鍵字。
        例如：'我想看看 hermes/core/runtime.py 的內容' -> read_file
        """
        text_lower = text.lower()
        
        # 偵測路徑格式 (簡單正則)
        path_match = re.search(r'([a-zA-Z0-9_\-\./]+\.(py|md|txt|json|yaml|yml|html|css|js|ts|toml))', text)
        
        if path_match:
            path = path_match.group(1)
            # 判斷動作意圖
            if any(k in text_lower for k in ["讀取", "讀", "查看", "分析", "read", "view", "cat", "open"]):
                return ToolPlan(tool="read_file", args={"file_path": path}, reason="Heuristic: read file keyword detected")
        
        # 偵測目錄列出意圖
        if any(k in text_lower for k in ["列出", "目錄", "清單", "ls", "list", "dir"]):
            # 嘗試抓取目錄路徑，若無則預設為 "."
            dir_match = re.search(r'目錄\s*([a-zA-Z0-9_\-\./]+)', text)
            target_dir = dir_match.group(1) if dir_match else "."
            return ToolPlan(tool="list_files", args={"directory": target_dir}, reason="Heuristic: list directory keyword detected")
            
        return None
