from pathlib import Path
import unittest
import io
import re
import hashlib
from typing import Optional, Any, List, Dict
from hermes.harness.constraints import ConstraintValidator
from hermes.core.types import ToolResult
from hermes.harness.patch import PatchProposal, FileChange
from hermes.harness.diff_engine import DiffEngine
from hermes.harness.approval import ApprovalManager
from hermes.harness.shell import GovernedShellExecutor
from hermes.markdown.report import extract_markdown_toc, summarize_markdown_report

class SafeExecutor:
    """
    安全執行器 V2.2: 具備 Patch 治理能力的 L3-α 執行環境。
    """
    def __init__(self, constraints: ConstraintValidator):
        self.constraints = constraints
        self.max_read_chars = 12000
        self.approval_manager = ApprovalManager()
        self.diff_engine = DiffEngine()
        self.shell_executor = GovernedShellExecutor(self.constraints)
        self.shell_approval_manager = self.shell_executor.approval_manager

    # --- 唯讀工具 (V1/V2.1) ---
    def read_file(self, path: str, max_chars: Optional[int] = None) -> ToolResult:
        limit = max_chars or self.max_read_chars
        is_safe, target_path_str = self.constraints.validate_path(path)
        if not is_safe:
            return ToolResult(ok=False, tool="read_file", summary="Access Denied", error=target_path_str)
        try:
            target_path = Path(target_path_str)
            if not target_path.is_file():
                return ToolResult(ok=False, tool="read_file", summary="Not a file", error="Target is not a file.")
            with open(target_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read(limit + 1)
            return ToolResult(ok=True, tool="read_file", summary="Read success", content=content[:limit])
        except Exception as e:
            return ToolResult(ok=False, tool="read_file", summary="Read Error", error=str(e))

    def list_files(self, path: str = ".") -> ToolResult:
        is_safe, target_path_str = self.constraints.validate_path(path)
        if not is_safe:
            return ToolResult(ok=False, tool="list_files", summary="Access Denied", error=target_path_str)
        try:
            items = [f"{'[D] ' if i.is_dir() else '[F] '}{i.name}" for i in list(Path(target_path_str).iterdir())]
            return ToolResult(ok=True, tool="list_files", summary="List success", content="\n".join(items))
        except Exception as e:
            return ToolResult(ok=False, tool="list_files", summary="List Error", error=str(e))

    def grep_search(self, query: str, path: str = ".") -> ToolResult:
        is_safe, target_path_str = self.constraints.validate_path(path)
        if not is_safe: return ToolResult(ok=False, tool="grep_search", summary="Access Denied", error=target_path_str)
        results = []
        try:
            root = Path(target_path_str)
            for p in root.rglob('*'):
                if any(seg in p.parts for seg in self.constraints.forbidden_segments): continue
                if p.is_file() and p.suffix.lower() in self.constraints.allowed_extensions:
                    with open(p, 'r', encoding='utf-8', errors='ignore') as f:
                        for i, line in enumerate(f, 1):
                            if query.lower() in line.lower():
                                results.append(f"{p.relative_to(root)}:{i}: {line.strip()}")
                if len(results) >= 100: break
            return ToolResult(ok=True, tool="grep_search", summary=f"Found {len(results)} matches", content="\n".join(results))
        except Exception as e: return ToolResult(ok=False, tool="grep_search", summary="Error", error=str(e))

    def read_markdown_report(self, path: str, max_chars: Optional[int] = None) -> ToolResult:
        read = self.read_file(path=path, max_chars=max_chars)
        if not read.ok:
            return ToolResult(ok=False, tool="read_markdown_report", summary=read.summary, error=read.error)
        report = summarize_markdown_report(read.content)
        return ToolResult(
            ok=True,
            tool="read_markdown_report",
            summary=f"Markdown report read: {report['title']}",
            content=read.content,
            metadata=report,
        )

    def preview_report(self, path: str, max_chars: Optional[int] = None) -> ToolResult:
        result = self.read_markdown_report(path=path, max_chars=max_chars)
        if not result.ok:
            return ToolResult(ok=False, tool="preview_report", summary=result.summary, error=result.error)
        preview_lines = [
            f"# {result.metadata.get('title', 'Markdown report')}",
            "",
            "## TOC",
            *[f"- L{item['level']} {item['text']} (line {item['line']})" for item in result.metadata.get("toc", [])],
            "",
            "## Summary",
            result.metadata.get("summary", ""),
        ]
        return ToolResult(
            ok=True,
            tool="preview_report",
            summary=f"Markdown preview prepared: {result.metadata.get('title', 'Markdown report')}",
            content="\n".join(preview_lines),
            metadata=result.metadata,
        )

    def extract_markdown_toc(self, path: str) -> ToolResult:
        read = self.read_file(path=path)
        if not read.ok:
            return ToolResult(ok=False, tool="extract_markdown_toc", summary=read.summary, error=read.error)
        toc = extract_markdown_toc(read.content)
        return ToolResult(
            ok=True,
            tool="extract_markdown_toc",
            summary=f"Extracted {len(toc)} headings",
            content="\n".join([f"L{item['level']} {item['text']} (line {item['line']})" for item in toc]),
            metadata={"toc": toc},
        )

    def propose_leaf_inline_preview(self, path: str) -> ToolResult:
        is_safe, target_path_str = self.constraints.validate_path(path)
        if not is_safe:
            return ToolResult(ok=False, tool="propose_leaf_inline_preview", summary="Access Denied", error=target_path_str)
        target = Path(target_path_str)
        if not target.is_file():
            return ToolResult(ok=False, tool="propose_leaf_inline_preview", summary="Not a file", error="Target is not a file.")
        command = f"leaf --inline {path}"
        return ToolResult(
            ok=True,
            tool="propose_leaf_inline_preview",
            summary="Leaf inline preview proposal created",
            content=(
                "Optional external viewer proposal only. Hermes will not install or execute Leaf automatically.\n"
                f"Command: {command}\n"
                "Risk: read-only external CLI preview. Execution must go through governed shell approval if used."
            ),
            metadata={
                "command": command,
                "permission": "read",
                "executes": False,
                "requires_approval": True,
            },
        )

    def generate_design_artifact(self, goal: str, path: str = ".") -> ToolResult:
        """
        產生設計/生成項目的安全草案，不寫入硬碟。
        """
        is_safe, target_path_str = self.constraints.validate_path(path)
        if not is_safe:
            return ToolResult(ok=False, tool="generate_design_artifact", summary="Access Denied", error=target_path_str)

        cleaned_goal = (goal or "").strip()
        if not cleaned_goal:
            return ToolResult(ok=False, tool="generate_design_artifact", summary="Missing goal", error="Design goal is required.")

        content = "\n".join([
            "# Hermes 生成設計產出",
            "",
            f"## 生成目標",
            cleaned_goal,
            "",
            "## 使用者價值",
            "- 讓使用者可以從一句需求得到可執行的設計方向。",
            "- 先產出可檢視的方案，再由使用者決定是否進入 Patch 寫入流程。",
            "",
            "## 建議產出結構",
            "1. 目標與受眾",
            "2. 核心功能",
            "3. 資訊架構與流程",
            "4. 視覺風格與互動狀態",
            "5. 驗收標準",
            "",
            "## 安全邊界",
            "- 此工具只生成文字方案，不會寫入、覆蓋或刪除檔案。",
            "- 需要落地成檔案時，必須走 propose_patch 與使用者批准。",
            "",
            "## 下一步",
            "請 Hermes 依此方案產生具體頁面、元件、文案或 patch proposal。"
        ])
        return ToolResult(
            ok=True,
            tool="generate_design_artifact",
            summary="Design artifact generated",
            content=content,
            metadata={"path": target_path_str}
        )

    def create_project_workspace(self, name: str = "generated-project", brief: str = "") -> ToolResult:
        """
        建立使用者生成項目的隔離工作區，只允許寫入 user_projects 底下。
        """
        safe_name = re.sub(r"[^a-zA-Z0-9_-]+", "-", (name or "generated-project").strip()).strip("-")
        if not safe_name:
            safe_name = "generated-project"

        relative_project_path = Path("user_projects") / safe_name
        is_safe, target_path_str = self.constraints.validate_path(str(relative_project_path))
        if not is_safe:
            return ToolResult(ok=False, tool="create_project_workspace", summary="Access Denied", error=target_path_str)

        try:
            project_dir = Path(target_path_str)
            project_dir.mkdir(parents=True, exist_ok=True)

            cleaned_brief = (brief or "").strip() or "使用者尚未提供詳細需求。"
            readme = "\n".join([
                f"# {safe_name}",
                "",
                "這是 Hermes 建立的使用者專案工作區。",
                "",
                "## 安全邊界",
                "- 此資料夾位於 user_projects 底下，不會改動 Hermes 原始碼。",
                "- 後續若要寫入程式碼，應繼續使用受控工具或 patch approval 流程。",
                "",
                "## 使用者需求",
                cleaned_brief,
                ""
            ])
            design_brief = "\n".join([
                "# Design Brief",
                "",
                "## Goal",
                cleaned_brief,
                "",
                "## Next Actions",
                "1. 產生頁面/功能規格。",
                "2. 產生可檢視的檔案草案。",
                "3. 執行測試或人工驗收。",
                ""
            ])

            (project_dir / "README.md").write_text(readme, encoding="utf-8")
            (project_dir / "design_brief.md").write_text(design_brief, encoding="utf-8")

            display_path = relative_project_path.as_posix()
            return ToolResult(
                ok=True,
                tool="create_project_workspace",
                summary="Project workspace created",
                content=f"Created isolated project workspace: {display_path}\nFiles:\n- README.md\n- design_brief.md",
                metadata={"path": str(project_dir)}
            )
        except Exception as e:
            return ToolResult(ok=False, tool="create_project_workspace", summary="Create Failed", error=str(e))

    def generate_static_site(self, name: str = "minimal_website", brief: str = "") -> ToolResult:
        """
        建立可直接開啟的靜態網站專案，只允許寫入 user_projects 底下。
        """
        workspace_result = self.create_project_workspace(name=name, brief=brief)
        if not workspace_result.ok:
            return ToolResult(
                ok=False,
                tool="generate_static_site",
                summary=workspace_result.summary,
                error=workspace_result.error,
                metadata=workspace_result.metadata,
            )

        project_dir = Path(workspace_result.metadata["path"])
        site_title = self._title_from_brief(brief)
        html = self._build_static_site_html(site_title)
        css = self._build_static_site_css()

        try:
            (project_dir / "index.html").write_text(html, encoding="utf-8")
            (project_dir / "styles.css").write_text(css, encoding="utf-8")
            readme = project_dir / "README.md"
            existing = readme.read_text(encoding="utf-8") if readme.exists() else f"# {name}\n"
            if "index.html" not in existing:
                existing += "\n## 已建立檔案\n- `index.html`：主頁面檔\n- `styles.css`：簡約風格樣式表\n- `design_brief.md`：設計需求簡報\n"
            readme.write_text(existing, encoding="utf-8")

            content = "\n".join([
                f"Generated static site: user_projects/{project_dir.name}",
                "Files:",
                "- index.html",
                "- styles.css",
                "- README.md",
                "- design_brief.md",
            ])
            return ToolResult(
                ok=True,
                tool="generate_static_site",
                summary="Static site generated",
                content=content,
                metadata={
                    "path": str(project_dir),
                    "files": ["index.html", "styles.css", "README.md", "design_brief.md"],
                },
            )
        except Exception as e:
            return ToolResult(ok=False, tool="generate_static_site", summary="Generate Failed", error=str(e))

    def _title_from_brief(self, brief: str) -> str:
        return "Minimal Website" if not brief else "Minimal Website"

    def _build_static_site_html(self, title: str) -> str:
        return f"""<!doctype html>
<html lang="zh-Hant">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title}</title>
  <link rel="stylesheet" href="styles.css">
</head>
<body>
  <header class="site-header">
    <a class="brand" href="#">Minimal</a>
    <nav class="nav" aria-label="主要導覽">
      <a href="#work">作品</a>
      <a href="#about">關於</a>
      <a href="#contact">聯絡</a>
    </nav>
  </header>
  <main>
    <section class="hero">
      <p class="eyebrow">Local-first static site</p>
      <h1>乾淨、快速、專注的本地網站。</h1>
      <p class="lead">這是 Hermes 生成的簡約風靜態網站，包含可直接開啟的 HTML 與現代化 CSS。</p>
      <div class="actions">
        <a class="button primary" href="#work">查看內容</a>
        <a class="button" href="#contact">聯絡我們</a>
      </div>
    </section>
    <section class="section" id="work">
      <div class="section-heading">
        <p class="eyebrow">Highlights</p>
        <h2>簡約但完整的起點</h2>
      </div>
      <div class="feature-grid">
        <article class="feature"><span>01</span><h3>清楚架構</h3><p>首頁、內容、關於與聯絡區塊已就緒。</p></article>
        <article class="feature"><span>02</span><h3>響應式</h3><p>桌機與手機都能維持舒適閱讀節奏。</p></article>
        <article class="feature"><span>03</span><h3>易擴充</h3><p>純 HTML/CSS，適合後續加上互動或部署。</p></article>
      </div>
    </section>
    <section class="section split" id="about">
      <h2>少即是多，但不是空白。</h2>
      <p>留白、清楚字級和穩定色彩讓內容保持主角。這個骨架可延伸成個人網站、產品頁或作品集。</p>
    </section>
    <section class="contact" id="contact">
      <p class="eyebrow">Contact</p>
      <h2>下一步，把它變成正式專案。</h2>
      <a class="button primary" href="mailto:hello@example.com">hello@example.com</a>
    </section>
  </main>
</body>
</html>
"""

    def _build_static_site_css(self) -> str:
        return """:root {
  color-scheme: light;
  --bg: #f7f6f1;
  --surface: #ffffff;
  --text: #151515;
  --muted: #6b6f76;
  --line: #dfddd5;
  --accent: #0f766e;
  --shadow: 0 18px 60px rgba(22, 27, 29, 0.08);
}
* { box-sizing: border-box; }
html { scroll-behavior: smooth; }
body {
  margin: 0;
  font-family: Inter, "Noto Sans TC", "Microsoft JhengHei", system-ui, sans-serif;
  background: var(--bg);
  color: var(--text);
  line-height: 1.65;
}
a { color: inherit; text-decoration: none; }
.site-header {
  position: sticky;
  top: 0;
  z-index: 10;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
  padding: 20px clamp(20px, 5vw, 72px);
  border-bottom: 1px solid rgba(223, 221, 213, 0.8);
  background: rgba(247, 246, 241, 0.88);
  backdrop-filter: blur(14px);
}
.brand { font-size: 18px; font-weight: 800; letter-spacing: 0; }
.nav { display: flex; gap: 18px; color: var(--muted); font-size: 14px; }
main { width: min(1120px, calc(100% - 40px)); margin: 0 auto; }
.hero {
  min-height: 72vh;
  display: flex;
  flex-direction: column;
  justify-content: center;
  padding: 80px 0 56px;
}
.eyebrow {
  margin: 0 0 14px;
  color: var(--accent);
  font-size: 13px;
  font-weight: 800;
  text-transform: uppercase;
}
h1, h2, h3, p { overflow-wrap: anywhere; }
h1 {
  max-width: 820px;
  margin: 0;
  font-size: clamp(42px, 8vw, 92px);
  line-height: 0.98;
  letter-spacing: 0;
}
.lead { max-width: 680px; margin: 28px 0 0; color: var(--muted); font-size: 18px; }
.actions { display: flex; flex-wrap: wrap; gap: 12px; margin-top: 34px; }
.button {
  display: inline-flex;
  min-height: 46px;
  align-items: center;
  justify-content: center;
  padding: 0 18px;
  border: 1px solid var(--line);
  border-radius: 6px;
  background: var(--surface);
  font-weight: 800;
  box-shadow: var(--shadow);
}
.button.primary { border-color: var(--accent); background: var(--accent); color: #fff; }
.section { padding: 74px 0; border-top: 1px solid var(--line); }
h2 { margin: 0; font-size: clamp(28px, 4vw, 46px); line-height: 1.08; letter-spacing: 0; }
.feature-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 16px; }
.feature {
  min-height: 220px;
  padding: 24px;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: var(--surface);
  box-shadow: var(--shadow);
}
.feature span { color: var(--accent); font-size: 13px; font-weight: 900; }
.feature h3 { margin: 32px 0 8px; font-size: 22px; }
.feature p, .split p { color: var(--muted); }
.split { display: grid; grid-template-columns: 0.9fr 1.1fr; gap: 40px; align-items: start; }
.contact { margin: 72px 0; padding: 48px; border-radius: 8px; background: var(--text); color: #fff; }
.contact .eyebrow { color: #7dd3ca; }
@media (max-width: 760px) {
  .site-header { align-items: flex-start; flex-direction: column; }
  .feature-grid, .split { grid-template-columns: 1fr; }
  .hero { min-height: auto; padding-top: 56px; }
  .contact { padding: 30px; }
}
"""

    # --- 治理工具 (V2.2) ---
    def propose_patch(self, task: str, changes: List[Dict[str, Any]]) -> ToolResult:
        """
        提出 Patch 提議：將變更暫存在記憶體中，並產生 Diff。
        """
        try:
            file_changes = []
            for c in changes:
                path = c["path"]
                if c["operation"] == "delete":
                    return ToolResult(
                        ok=False,
                        tool="propose_patch",
                        summary="Delete disabled",
                        error="Delete operation is disabled by Hermes safety policy."
                    )
                is_safe, target_path_str = self.constraints.validate_path(path)
                if not is_safe:
                    return ToolResult(ok=False, tool="propose_patch", summary="Access Denied", error=target_path_str)
                
                original_content = ""
                if c["operation"] == "modify":
                    with open(target_path_str, 'r', encoding='utf-8') as f:
                        original_content = f.read()
                    before_hash = self._hash_text(original_content)
                else:
                    before_hash = None
                
                file_changes.append(FileChange(
                    path=path,
                    operation=c["operation"],
                    reason=c.get("reason", ""),
                    before_hash=before_hash,
                    original=original_content,
                    replacement=c.get("replacement", "")
                ))
            
            proposal = PatchProposal(task_id=task, changes=file_changes)
            self.approval_manager.register_proposal(proposal)
            
            diff = self.diff_engine.generate_patch_diff(proposal)
            return ToolResult(
                ok=True, 
                tool="propose_patch", 
                summary=f"Proposal {proposal.id} created. Approval REQUIRED.",
                content=diff,
                metadata={"patch_id": proposal.id}
            )
        except Exception as e:
            return ToolResult(ok=False, tool="propose_patch", summary="Proposal Failed", error=str(e))

    def apply_approved_patch(self, patch_id: str, approval_token: str) -> ToolResult:
        """
        套用已授權的 Patch：執行實體寫入。
        """
        if not self.approval_manager.validate(patch_id, approval_token):
            return ToolResult(ok=False, tool="apply_approved_patch", summary="Unauthorized", error="Invalid or expired token.")
        
        proposal = self.approval_manager.pending_patches.get(patch_id)
        results = []
        try:
            for change in proposal.changes:
                is_safe, target_path_str = self.constraints.validate_path(change.path)
                if not is_safe:
                    return ToolResult(ok=False, tool="apply_approved_patch", summary="Safety Violation during apply", error=target_path_str)
                
                target_path = Path(target_path_str)
                if change.operation == "modify" or change.operation == "create":
                    if change.operation == "modify":
                        current_content = target_path.read_text(encoding='utf-8')
                        if change.before_hash and self._hash_text(current_content) != change.before_hash:
                            return ToolResult(
                                ok=False,
                                tool="apply_approved_patch",
                                summary="Stale patch",
                                error=f"Stale patch: {change.path} changed after proposal."
                            )
                    # 確保目錄存在
                    target_path.parent.mkdir(parents=True, exist_ok=True)
                    with open(target_path, 'w', encoding='utf-8') as f:
                        f.write(change.replacement)
                
                results.append(f"Applied: {change.path}")
            
            proposal.status = "applied"
            return ToolResult(ok=True, tool="apply_approved_patch", summary=f"Patch {patch_id} applied successfully.", content="\n".join(results))
        except Exception as e:
            proposal.status = "failed"
            return ToolResult(ok=False, tool="apply_approved_patch", summary="Apply Failed", error=str(e))

    def run_tests(self, path: str = "tests") -> ToolResult:
        is_safe, target_path_str = self.constraints.validate_path(path)
        if not is_safe: return ToolResult(ok=False, tool="run_tests", summary="Access Denied", error=target_path_str)
        try:
            loader = unittest.TestLoader()
            suite = loader.discover(target_path_str, pattern="test_*.py")
            stream = io.StringIO()
            runner = unittest.TextTestRunner(stream=stream, verbosity=2)
            result = runner.run(suite)
            return ToolResult(ok=result.wasSuccessful(), tool="run_tests", summary=f"Tests: {result.testsRun}, Fail: {len(result.failures)}", content=stream.getvalue())
        except Exception as e: return ToolResult(ok=False, tool="run_tests", summary="Error", error=str(e))

    def execute_shell(self, command: str) -> ToolResult:
        return ToolResult(ok=False, tool="execute_shell", summary="Disabled", error="Shell is DISABLED.")

    def propose_shell_command(self, command: str, reason: str = "", cwd: str = ".") -> ToolResult:
        return self.shell_executor.propose(command=command, reason=reason, cwd=cwd)

    def execute_approved_shell(self, proposal_id: str, approval_token: str, timeout_seconds: int = 120) -> ToolResult:
        return self.shell_executor.execute(
            proposal_id=proposal_id,
            approval_token=approval_token,
            timeout_seconds=timeout_seconds,
        )

    def _hash_text(self, content: str) -> str:
        return hashlib.sha256(content.encode("utf-8")).hexdigest()
