import re

from hermes.core.types import ToolResult
from hermes.harness.tools import ToolRegistry
from hermes.management.auditor import ManagementAuditor
from hermes.management.decision import ExecutionResult, ExecutionStep, ManagedTaskPlan
from hermes.management.policy import ManagementPolicy


class ManagementOrchestrator:
    """Coordinates risk classification, step planning, execution, and audit."""

    def __init__(
        self,
        tools: ToolRegistry,
        policy: ManagementPolicy | None = None,
        auditor: ManagementAuditor | None = None,
    ):
        self.tools = tools
        self.policy = policy or ManagementPolicy()
        self.auditor = auditor or ManagementAuditor(tool_registry=tools)

    def plan(self, task: str) -> ManagedTaskPlan:
        decision = self.policy.classify_task(task)
        steps = self._build_steps(decision)
        return ManagedTaskPlan(decision=decision, steps=steps)

    def execute(self, plan: ManagedTaskPlan) -> ExecutionResult:
        if plan.decision.rejected:
            audit = self.auditor.verify(plan, [])
            return ExecutionResult(ok=False, plan=plan, step_results=[], audit=audit, error="Task rejected by management policy.")

        step_results = []
        for step in plan.steps:
            if step.tool is None:
                continue

            tool_spec = self.tools.get_tool(step.tool)
            if not tool_spec:
                result = ToolResult(ok=False, tool=step.tool, summary="Tool not found", error=f"Tool {step.tool} not found")
            else:
                result = tool_spec.handler(**step.args)

            step_results.append((step, result))
            if not result.ok:
                break

        audit = self.auditor.verify(plan, step_results)
        return ExecutionResult(
            ok=audit.verified,
            plan=plan,
            step_results=step_results,
            audit=audit,
            error="; ".join(audit.failed_criteria),
        )

    def _build_steps(self, decision) -> list[ExecutionStep]:
        task = decision.task
        if decision.intent == "generate_static_site":
            project_name = self._extract_site_name(task)
            return [
                ExecutionStep(
                    id="S1",
                    type="write",
                    tool="generate_static_site",
                    args={"name": project_name, "brief": task},
                    reason="建立可直接開啟的本地靜態網站，產生 HTML 與 CSS 檔案。",
                    expected="user_projects/<project> 包含 index.html、styles.css、README.md 與 design_brief.md。",
                ),
                ExecutionStep(
                    id="S2",
                    type="verify",
                    tool="list_files",
                    args={"path": f"user_projects/{project_name}"},
                    reason="確認網站檔案實際存在，避免回覆未寫入的檔案。",
                    expected="清單包含 index.html 與 styles.css。",
                ),
            ]

        if decision.intent == "create_project":
            return [
                ExecutionStep(
                    id="S1",
                    type="write",
                    tool="create_project_workspace",
                    args={"name": self._extract_project_name(task), "brief": task},
                    reason="建立隔離的使用者專案工作區，避免改動 Hermes 原始碼。",
                    expected="user_projects/<project> 存在，且包含 README.md 與 design_brief.md。",
                ),
                ExecutionStep(
                    id="S2",
                    type="verify",
                    tool="list_files",
                    args={"path": f"user_projects/{self._extract_project_name(task)}"},
                    reason="確認專案工作區實際建立了預期檔案。",
                    expected="清單包含 README.md 與 design_brief.md。",
                ),
            ]

        if decision.intent == "read_workspace":
            paths = self._extract_file_paths(task) or ["README.md"]
            return [
                ExecutionStep(
                    id=f"S{index}",
                    type="read",
                    tool="read_file",
                    args={"path": path},
                    reason="讀取使用者指定的 workspace 檔案。",
                    expected="工具回傳檔案內容。",
                )
                for index, path in enumerate(paths, start=1)
            ]

        if decision.intent == "search_workspace":
            return [
                ExecutionStep(
                    id="S1",
                    type="read",
                    tool="grep_search",
                    args={"query": self._extract_query(task), "path": "."},
                    reason="搜尋 workspace 內的指定關鍵字。",
                    expected="工具回傳搜尋結果或空結果。",
                )
            ]

        if decision.intent == "run_tests":
            return [
                ExecutionStep(
                    id="S1",
                    type="test",
                    tool="run_tests",
                    args={"path": "tests"},
                    reason="執行測試以驗證目前系統狀態。",
                    expected="工具回傳測試數量與失敗數。",
                )
            ]

        if decision.intent == "mcp_read":
            tool_name = self._select_read_only_mcp_tool(task)
            return [
                ExecutionStep(
                    id="S1",
                    type="read",
                    tool=tool_name,
                    args=self._extract_mcp_args(task, tool_name),
                    reason="透過 ToolRegistry 呼叫受治理的 read-only MCP 工具。",
                    expected="MCP 工具回傳外部資源內容，並留下 MCP Trace。",
                )
            ]

        if decision.intent == "modify_core":
            return [
                ExecutionStep(
                    id="S1",
                    type="generate",
                    tool="generate_design_artifact",
                    args={"goal": f"針對高風險核心修改產生 patch plan，不直接改檔：{task}", "path": "."},
                    reason="核心檔案修改必須先產生可審查方案，不可直接寫入。",
                    expected="產生方案或 patch plan 草案。",
                )
            ]

        if decision.intent == "propose_shell_command":
            return [
                ExecutionStep(
                    id="S1",
                    type="generate",
                    tool="propose_shell_command",
                    args={
                        "command": self._extract_shell_command(task),
                        "reason": task,
                        "cwd": ".",
                    },
                    reason="建立受治理 shell 指令提案，不直接執行。",
                    expected="產生 pending shell proposal，等待使用者批准。",
                )
            ]

        return []

    def _extract_file_path(self, task: str) -> str | None:
        paths = self._extract_file_paths(task)
        return paths[0] if paths else None

    def _extract_file_paths(self, task: str) -> list[str]:
        candidates: list[str] = []
        explicit_stems = set()
        pattern = r"([a-zA-Z0-9_\-\./\\]+\.(py|md|txt|json|yaml|yml|html|css|js|ts|toml|bat))"
        for match in re.finditer(pattern, task):
            explicit_path = match.group(1).replace("\\", "/")
            candidates.append(explicit_path)
            explicit_stems.add(explicit_path.rsplit("/", 1)[-1].split(".", 1)[0].lower())

        for token in re.findall(r"[a-zA-Z][a-zA-Z0-9_-]{2,}", task):
            if "." in token or token.lower() in explicit_stems:
                continue
            resolved = self._resolve_bare_file_name(token)
            candidates.extend(resolved)

        return self._dedupe_existing_first(candidates)

    def _resolve_bare_file_name(self, token: str) -> list[str]:
        root = self._workspace_root()
        if not root:
            return []

        matches = []
        wanted = {token.lower(), f"{token.lower()}.md"}
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            if any(part in {".git", ".env", ".venv", "node_modules", "__pycache__"} for part in path.parts):
                continue
            if path.name.lower() in wanted or path.stem.lower() == token.lower():
                matches.append(path.relative_to(root).as_posix())

        matches.sort(key=lambda p: (0 if p.startswith("user_projects/") else 1, len(p), p))
        return matches[:2]

    def _workspace_root(self):
        read_tool = self.tools.get_tool("read_file")
        executor = getattr(read_tool.handler, "__self__", None) if read_tool else None
        constraints = getattr(executor, "constraints", None)
        return getattr(constraints, "workspace_root", None)

    def _dedupe_existing_first(self, paths: list[str]) -> list[str]:
        seen = set()
        result = []
        for path in paths:
            normalized = path.replace("\\", "/").strip()
            if not normalized or normalized in seen:
                continue
            seen.add(normalized)
            result.append(normalized)
        return result

    def _extract_query(self, task: str) -> str:
        quoted = re.search(r"['\"]([^'\"]+)['\"]", task)
        if quoted:
            return quoted.group(1)
        return task.strip()

    def _extract_project_name(self, task: str) -> str:
        match = re.search(r"(?:專案|project)\s*[:：]?\s*([a-zA-Z0-9_-]+)", task, re.IGNORECASE)
        if match:
            return match.group(1)
        return "generated-project"

    def _extract_site_name(self, task: str) -> str:
        match = re.search(r"(?:網站|website|site)\s*[:：]?\s*([a-zA-Z0-9_-]+)", task, re.IGNORECASE)
        if match:
            return match.group(1)
        if "簡約" in task or "minimal" in task.lower():
            return "minimal_website"
        return "generated_site"

    def _select_read_only_mcp_tool(self, task: str) -> str:
        lowered = task.lower()
        candidates = []
        for name, spec in self.tools.tools.items():
            if not name.startswith("mcp.") or spec.permission != "read":
                continue
            score = 0
            if "github" in lowered and ".github." in name:
                score += 10
            if "issue" in lowered and "issue" in name:
                score += 6
            if "note" in lowered and "note" in name:
                score += 6
            if "read" in name:
                score += 2
            candidates.append((score, name))
        if not candidates:
            return "mcp.unavailable.read"
        candidates.sort(key=lambda item: (-item[0], item[1]))
        return candidates[0][1]

    def _extract_mcp_args(self, task: str, tool_name: str) -> dict:
        if "issue" in tool_name:
            number = re.search(r"#?(\d+)", task)
            args = {}
            if number:
                args["issue_number"] = int(number.group(1))
            return args
        if "read_file" in tool_name:
            return {"path": (self._extract_file_path(task) or "README.md")}
        if "list_files" in tool_name:
            return {"path": "."}
        if "search_files" in tool_name:
            return {"query": self._extract_query(task), "path": "."}
        if "note" in tool_name:
            return {"query": task}
        return {"query": task}

    def _extract_shell_command(self, task: str) -> str:
        normalized = task.strip()
        git_clone = re.search(r"(git\s+clone\s+\S+(?:\s+\S+)?)", normalized, re.IGNORECASE)
        if git_clone:
            return git_clone.group(1)
        github_clone = re.search(r"clone\s+(https://github\.com/\S+)(?:\s+(?:到|to)\s+([a-zA-Z0-9_\-./\\]+))?", normalized, re.IGNORECASE)
        if github_clone:
            target = f" {github_clone.group(2)}" if github_clone.group(2) else ""
            return f"git clone {github_clone.group(1)}{target}"
        npm = re.search(r"(npm\s+(?:install|run)\s+\S+)", normalized, re.IGNORECASE)
        if npm:
            return npm.group(1)
        python = re.search(r"((?:python|py)\s+-m\s+\S+(?:\s+\S+)*)", normalized, re.IGNORECASE)
        if python:
            return python.group(1)
        ollama = re.search(r"(ollama\s+(?:list|show)(?:\s+\S+)*)", normalized, re.IGNORECASE)
        if ollama:
            return ollama.group(1)
        return normalized
