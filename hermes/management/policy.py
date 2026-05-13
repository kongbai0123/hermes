import re
from pathlib import Path

from hermes.management.decision import DecisionPacket


class ManagementPolicy:
    """Deterministic risk gate for Hermes managed execution."""

    def classify_task(self, task: str) -> DecisionPacket:
        text = (task or "").strip()
        lowered = text.lower()

        if self._contains_any(lowered, ["刪除", "删除", "delete", "remove", "rm ", "del "]):
            return self._decision(
                text,
                "rejected_destructive_request",
                "reject",
                requires_tools=False,
                requires_write=True,
                requires_user_approval=True,
                criteria=["拒絕刪除或破壞性操作"],
                notes={"reason": "destructive operation is disabled"},
            )

        if self._is_governed_shell_request(lowered):
            return self._decision(
                text,
                "propose_shell_command",
                "requires_user_approval",
                requires_tools=True,
                requires_write=False,
                requires_user_approval=True,
                criteria=[
                    "只能產生 shell proposal",
                    "不得直接執行 shell",
                    "命令必須符合 governed shell allowlist",
                    "真正執行必須使用 approval token",
                ],
                notes={"permission": "shell_execute"},
            )

        if self._contains_any(lowered, ["shell", "powershell", "cmd", "terminal", "curl", "wget", "pip install"]):
            return self._decision(
                text,
                "rejected_shell_request",
                "reject",
                requires_tools=False,
                requires_write=False,
                requires_user_approval=True,
                criteria=["拒絕未治理 shell 或外部下載"],
                notes={"reason": "shell is disabled before management governance is complete"},
            )

        if self._contains_any(lowered, ["apply patch", "套用 patch", "套用變更", "批准套用"]):
            return self._decision(
                text,
                "apply_patch",
                "requires_user_approval",
                requires_tools=True,
                requires_write=True,
                requires_user_approval=True,
                criteria=["必須提供 approval token", "只能套用已批准 patch"],
            )

        if self._is_core_modify_request(text, lowered):
            return self._decision(
                text,
                "modify_core",
                "high",
                requires_tools=True,
                requires_write=True,
                requires_user_approval=True,
                criteria=["只能產生 patch proposal", "不得直接修改 Hermes 核心檔案"],
            )

        if self._contains_any(lowered, ["執行測試", "跑測試", "運行測試", "run_tests", "pytest", "unittest", "run tests"]):
            return self._decision(
                text,
                "run_tests",
                "medium",
                requires_tools=True,
                requires_write=False,
                requires_user_approval=False,
                criteria=["測試工具必須回傳結果", "失敗時必須回報錯誤摘要"],
            )

        if self._contains_any(lowered, ["mcp", "github issue", "外部工具"]):
            return self._decision(
                text,
                "mcp_read",
                "low",
                requires_tools=True,
                requires_write=False,
                requires_user_approval=False,
                criteria=["MCP 工具必須經 ToolRegistry 執行", "只允許 read-only MCP tool", "MCP 呼叫必須留下 Trace"],
                notes={"requires_mcp": True, "external_tool_risk": "low"},
            )

        wants_site = self._contains_any(lowered, ["網站", "網頁", "頁面", "website", "site", "static site"])
        wants_build = self._contains_any(lowered, ["架設", "建立", "新增", "create", "生成", "製作", "產生", "做一個", "本地"])
        if wants_site and wants_build:
            return self._decision(
                text,
                "generate_static_site",
                "medium",
                requires_tools=True,
                requires_write=True,
                requires_user_approval=False,
                criteria=[
                    "在 user_projects 底下建立隔離網站專案",
                    "必須實際產生 index.html",
                    "必須實際產生 styles.css",
                    "不可改動 Hermes 原始碼",
                    "回覆中只能列出工具結果證明存在的檔案",
                ],
            )

        wants_project = self._contains_any(lowered, ["建立", "新增", "create", "mkdir", "資料夾", "folder", "專案", "project"])
        wants_generation = self._contains_any(lowered, ["設計", "生成", "製作", "產生", "app", "application"])
        if wants_project and wants_generation:
            return self._decision(
                text,
                "create_project",
                "medium",
                requires_tools=True,
                requires_write=True,
                requires_user_approval=False,
                criteria=[
                    "在 user_projects 底下建立隔離專案",
                    "不可改動 Hermes 原始碼",
                    "回覆中必須列出實際建立的檔案",
                ],
            )

        if self._contains_any(lowered, ["搜尋", "grep", "search", "找"]):
            return self._decision(
                text,
                "search_workspace",
                "low",
                requires_tools=True,
                requires_write=False,
                requires_user_approval=False,
                criteria=["搜尋結果必須來自工具輸出"],
            )

        if self._looks_like_read_request(text, lowered):
            return self._decision(
                text,
                "read_workspace",
                "low",
                requires_tools=True,
                requires_write=False,
                requires_user_approval=False,
                criteria=["讀取結果必須來自 workspace 內檔案"],
            )

        return self._decision(
            text,
            "general_chat",
            "low",
            requires_tools=False,
            requires_write=False,
            requires_user_approval=False,
            criteria=["直接回答使用者問題"],
        )

    def _decision(
        self,
        task: str,
        intent: str,
        risk_level: str,
        requires_tools: bool,
        requires_write: bool,
        requires_user_approval: bool,
        criteria: list[str],
        notes: dict | None = None,
    ) -> DecisionPacket:
        return DecisionPacket(
            task=task,
            intent=intent,
            risk_level=risk_level,
            requires_tools=requires_tools,
            requires_write=requires_write,
            requires_user_approval=requires_user_approval,
            requires_mcp=bool((notes or {}).get("requires_mcp", False)),
            external_tool_risk=(notes or {}).get("external_tool_risk", "none"),
            success_criteria=criteria,
            notes=notes or {},
        )

    def _contains_any(self, text: str, keywords: list[str]) -> bool:
        return any(keyword in text for keyword in keywords)

    def _looks_like_read_request(self, text: str, lowered: str) -> bool:
        has_file = re.search(r"([a-zA-Z0-9_\-\./\\]+\.(py|md|txt|json|yaml|yml|html|css|js|ts|toml|bat))", text)
        return bool(has_file and self._contains_any(lowered, ["讀", "看", "read", "view", "cat", "摘要"]))

    def _is_core_modify_request(self, text: str, lowered: str) -> bool:
        wants_modify = self._contains_any(lowered, ["修改", "改寫", "更新", "覆蓋", "寫入", "modify", "update", "edit"])
        normalized = text.replace("\\", "/").lower()
        path = Path(normalized)
        mentions_core = "hermes/" in normalized or "runtime.py" in path.name or "dashboard.html" in path.name
        return wants_modify and mentions_core

    def _is_governed_shell_request(self, lowered: str) -> bool:
        return self._contains_any(lowered, [
            "git clone",
            "github clone",
            "clone https://github.com",
            "npm install",
            "npm run",
            "python -m",
            "py -m",
            "node ",
            "ollama list",
            "ollama show",
        ])
