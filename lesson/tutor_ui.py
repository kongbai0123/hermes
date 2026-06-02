"""Browser-based teaching UI for LocalAgentTutor."""

from __future__ import annotations

import argparse
import contextlib
import io
import json
import os
import runpy
import subprocess
import sys
import threading
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from LocalAgentTutor import LESSONS, find_project_root


ROOT = find_project_root()
os.environ["LOCAL_AGENT_TUTOR_ROOT"] = str(ROOT)
NOTE_FILES = {
    "overview": ROOT / "README.md",
    "lessons": ROOT / "lessons" / "README.md",
    "workflows": ROOT / "notes" / "WORKFLOWS.md",
    "packaging": ROOT / "notes" / "PACKAGING.md",
}


def run_script(script: str, timeout: int = 90) -> dict:
    path = ROOT / script
    if not path.exists():
        return {"ok": False, "output": f"找不到課程檔案：{script}"}
    if getattr(sys, "frozen", False):
        return run_script_in_process(path)
    return run_command([sys.executable, str(path)], timeout=timeout)


def run_script_in_process(path: Path) -> dict:
    old_argv = sys.argv[:]
    old_stdin = sys.stdin
    output = io.StringIO()
    try:
        sys.argv = [str(path)]
        sys.stdin = io.StringIO("exit\n/exit\nquit\n")
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
            runpy.run_path(str(path), run_name="__main__")
    except SystemExit as exc:
        code = exc.code if isinstance(exc.code, int) else 0
        return {"ok": code == 0, "output": output.getvalue().strip() or f"結束代碼：{code}"}
    except Exception as exc:
        text = output.getvalue().strip()
        if text:
            text += "\n\n"
        text += f"執行失敗：{exc}"
        return {"ok": False, "output": text}
    finally:
        sys.argv = old_argv
        sys.stdin = old_stdin
    return {"ok": True, "output": output.getvalue().strip() or "執行完成。"}


def run_command(command: list[str], timeout: int = 90) -> dict:
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"
    try:
        completed = subprocess.run(
            command,
            cwd=ROOT,
            env=env,
            input="exit\n/exit\nquit\n",
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return {"ok": False, "output": "執行逾時。這堂課可能需要在終端機互動操作。"}
    except FileNotFoundError:
        return {"ok": False, "output": f"找不到命令：{command[0]}"}
    output = (completed.stdout + completed.stderr).strip()
    return {"ok": completed.returncode == 0, "output": output or f"結束代碼：{completed.returncode}"}


def run_agent(prompt: str) -> dict:
    if not prompt.strip():
        return {"ok": False, "output": "請先輸入問題。"}
    try:
        from agent.react import ReactAgent

        agent = ReactAgent.create()
        trace = io.StringIO()
        with contextlib.redirect_stdout(trace), contextlib.redirect_stderr(trace):
            answer = agent.answer(prompt)
        trace_text = trace.getvalue().strip()
        if trace_text:
            answer = f"{answer}\n\n---\nTool observation log:\n{trace_text}"
        return {"ok": True, "output": answer}
    except Exception as exc:
        return {"ok": False, "output": f"Agent 執行失敗：{exc}"}


def run_tests() -> dict:
    if not getattr(sys, "frozen", False):
        return run_command([sys.executable, "-m", "unittest", "discover", "-s", "workspace/sample_project"])

    import unittest

    output = io.StringIO()
    start_dir = str(ROOT / "workspace" / "sample_project")
    old_path = sys.path[:]
    try:
        sys.path.insert(0, start_dir)
        suite = unittest.defaultTestLoader.discover(start_dir)
        runner = unittest.TextTestRunner(stream=output, verbosity=1)
        result = runner.run(suite)
        return {"ok": result.wasSuccessful(), "output": output.getvalue().strip()}
    except Exception as exc:
        text = output.getvalue().strip()
        if text:
            text += "\n\n"
        text += f"測試執行失敗：{exc}"
        return {"ok": False, "output": text}
    finally:
        sys.path = old_path


class TutorHandler(BaseHTTPRequestHandler):
    server_version = "LocalAgentTutorUI/1.0"

    def do_GET(self) -> None:
        route = urlparse(self.path).path
        if route == "/":
            self.send_html(INDEX_HTML)
        elif route == "/api/lessons":
            self.send_json(
                {
                    "lessons": [
                        {
                            "number": index,
                            "code": lesson_id,
                            "title": title,
                            "script": script,
                            "summary": summary,
                        }
                        for index, (lesson_id, title, script, summary) in enumerate(LESSONS, start=1)
                    ]
                }
            )
        elif route == "/api/status":
            self.send_json({"root": str(ROOT), "python": sys.executable})
        elif route.startswith("/api/note/"):
            key = route.rsplit("/", 1)[-1]
            path = NOTE_FILES.get(key)
            if path is None or not path.exists():
                self.send_json({"ok": False, "content": "找不到筆記。"}, status=404)
            else:
                self.send_json({"ok": True, "content": path.read_text(encoding="utf-8", errors="replace")})
        else:
            self.send_json({"ok": False, "error": "Not found"}, status=404)

    def do_POST(self) -> None:
        route = urlparse(self.path).path
        body = self.read_json()
        if route == "/api/run-lesson":
            script = str(body.get("script", ""))
            self.send_json(run_script(script))
        elif route == "/api/run-tests":
            self.send_json(run_tests())
        elif route == "/api/agent":
            self.send_json(run_agent(str(body.get("prompt", ""))))
        elif route == "/api/open-folder":
            os.startfile(ROOT)
            self.send_json({"ok": True, "output": f"已開啟：{ROOT}"})
        else:
            self.send_json({"ok": False, "error": "Not found"}, status=404)

    def log_message(self, format: str, *args: object) -> None:
        return

    def read_json(self) -> dict:
        length = int(self.headers.get("Content-Length", "0"))
        if length == 0:
            return {}
        raw = self.rfile.read(length).decode("utf-8")
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            return {}
        return data if isinstance(data, dict) else {}

    def send_html(self, html: str) -> None:
        payload = html.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def send_json(self, data: dict, status: int = 200) -> None:
        payload = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)


INDEX_HTML = r"""<!doctype html>
<html lang="zh-Hant">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>LocalAgentTutor UI</title>
  <style>
    :root {
      --bg: #f6f7f9;
      --panel: #ffffff;
      --ink: #1f2937;
      --muted: #667085;
      --line: #d9dee7;
      --accent: #2563eb;
      --accent-soft: #eaf1ff;
      --ok: #0f766e;
      --warn: #b45309;
      --code: #111827;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: "Microsoft JhengHei", "Segoe UI", Arial, sans-serif;
      background: var(--bg);
      color: var(--ink);
    }
    header {
      padding: 18px 28px;
      border-bottom: 1px solid var(--line);
      background: var(--panel);
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
    }
    h1 { margin: 0; font-size: 22px; }
    .status { color: var(--muted); font-size: 13px; }
    main {
      display: grid;
      grid-template-columns: minmax(320px, 430px) minmax(420px, 1fr);
      min-height: calc(100vh - 74px);
    }
    aside {
      border-right: 1px solid var(--line);
      background: var(--panel);
      padding: 18px;
      overflow: auto;
    }
    section {
      padding: 18px;
      overflow: auto;
    }
    .toolbar {
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
      margin-bottom: 14px;
    }
    button {
      border: 1px solid var(--line);
      background: var(--panel);
      color: var(--ink);
      border-radius: 6px;
      padding: 8px 10px;
      font-size: 14px;
      cursor: pointer;
    }
    button.primary {
      border-color: var(--accent);
      background: var(--accent);
      color: white;
    }
    button:hover { border-color: var(--accent); }
    .lesson {
      width: 100%;
      text-align: left;
      margin-bottom: 8px;
      display: grid;
      grid-template-columns: 42px 1fr;
      gap: 8px;
      align-items: start;
    }
    .lesson.active {
      border-color: var(--accent);
      background: var(--accent-soft);
    }
    .num {
      color: var(--accent);
      font-weight: 700;
      font-variant-numeric: tabular-nums;
    }
    .lesson-title { font-weight: 700; margin-bottom: 4px; }
    .lesson-summary { color: var(--muted); font-size: 13px; line-height: 1.45; }
    .workspace {
      display: grid;
      grid-template-rows: auto auto 1fr;
      gap: 14px;
      min-height: calc(100vh - 110px);
    }
    .panel {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 14px;
    }
    h2 { margin: 0 0 8px; font-size: 18px; }
    .meta { color: var(--muted); font-size: 13px; margin-bottom: 12px; }
    .agent-row {
      display: grid;
      grid-template-columns: 1fr auto;
      gap: 8px;
    }
    input {
      border: 1px solid var(--line);
      border-radius: 6px;
      padding: 9px 10px;
      font-size: 14px;
      width: 100%;
    }
    pre {
      margin: 0;
      white-space: pre-wrap;
      word-break: break-word;
      background: var(--code);
      color: #f8fafc;
      border-radius: 8px;
      padding: 14px;
      min-height: 300px;
      max-height: 55vh;
      overflow: auto;
      font-size: 13px;
      line-height: 1.5;
    }
    .suggestions {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-top: 10px;
    }
    .suggestion {
      border-color: #b9c7dc;
      background: #f8fbff;
      color: #24466f;
      text-align: left;
      line-height: 1.35;
    }
    .hint-title {
      margin: 0 0 6px;
      color: var(--muted);
      font-size: 13px;
      font-weight: 700;
    }
    .note {
      background: #fffdf5;
      border-color: #f1d18a;
      color: #5f3b00;
    }
    @media (max-width: 900px) {
      main { grid-template-columns: 1fr; }
      aside { border-right: 0; border-bottom: 1px solid var(--line); max-height: 48vh; }
      .agent-row { grid-template-columns: 1fr; }
    }
  </style>
</head>
<body>
  <header>
    <div>
      <h1>LocalAgentTutor 教學式 UI</h1>
      <div class="status" id="status">載入中...</div>
    </div>
    <div class="toolbar">
      <button onclick="loadNote('overview')">課程總覽</button>
      <button onclick="loadNote('workflows')">實戰流程</button>
      <button onclick="runTests()">執行測試</button>
      <button onclick="openFolder()">開啟原始碼</button>
    </div>
  </header>
  <main>
    <aside>
      <div class="toolbar">
        <button class="primary" onclick="selectFirst()">從第一課開始</button>
        <button onclick="loadNote('packaging')">打包說明</button>
      </div>
      <div id="lessons"></div>
    </aside>
    <section>
      <div class="workspace">
        <div class="panel">
          <h2 id="lessonTitle">選擇一堂課</h2>
          <div class="meta" id="lessonMeta">左側課程可直接執行，也可以先閱讀筆記。</div>
          <div class="toolbar">
            <button class="primary" onclick="runSelectedLesson()">執行目前課程</button>
            <button onclick="loadNote('lessons')">查看課程指南</button>
          </div>
        </div>
        <div class="panel">
          <h2>快速體驗 Agent</h2>
          <div class="meta">輸入一個小任務，UI 會呼叫本機 ReAct agent。建議先問：請分析 workspace 裡的程式結構</div>
          <div class="agent-row">
            <input id="agentPrompt" value="請分析 workspace 裡的程式結構">
            <button onclick="askAgent()">送出給 Agent</button>
          </div>
        </div>
        <div class="panel">
          <h2>輸出與觀察</h2>
          <pre id="output">這裡會顯示課程輸出、測試結果、筆記或 Agent 回答。</pre>
          <div id="suggestionBlock" style="display:none">
            <div class="hint-title">下一步可以問</div>
            <div class="suggestions" id="suggestions"></div>
          </div>
        </div>
      </div>
    </section>
  </main>
  <script>
    let lessons = [];
    let selected = null;

    async function api(path, options = {}) {
      const res = await fetch(path, options);
      return await res.json();
    }

    const lessonHints = {
      "1-1": [
        "Ollama 的 /api/chat 和 /api/generate 差在哪？",
        "串流輸出 stream=True 是怎麼逐字顯示的？",
        "如果模型沒有回應，我應該先檢查哪些地方？"
      ],
      "1-2": [
        "為什麼 LLM 本身不會自動記住對話？",
        "對話記憶太長會造成什麼問題？",
        "System Prompt 和 User Prompt 的差別是什麼？"
      ],
      "1-3": [
        "為什麼工具呼叫要用 JSON 格式？",
        "如果模型輸出不是合法 JSON，要怎麼處理？",
        "工具執行結果 Observation 應該包含哪些資訊？"
      ],
      "1-4": [
        "ReAct 的 Thought、Action、Observation 各自負責什麼？",
        "為什麼 Agent 需要多步驟 loop？",
        "什麼情況應該停止工具呼叫並給 Final Answer？"
      ],
      "1-5": [
        "為什麼檔案工具一定要限制根目錄？",
        "讀檔、寫檔、刪檔的安全等級差在哪？",
        "如何避免 Agent 讀到不該讀的檔案？"
      ],
      "2-1": [
        "把模型呼叫封裝成 generate() 有什麼好處？",
        "temperature 參數會如何影響回答？",
        "如果要切換 gemma4 和 qwen-local，架構要怎麼設計？"
      ],
      "2-2": [
        "ConversationMemory 為什麼要限制 max_messages？",
        "記憶應該存原文、摘要，還是兩者都存？",
        "多輪對話中哪些內容最值得保留？"
      ],
      "2-3": [
        "工具 registry 是什麼設計模式？",
        "新增一個工具需要改哪些地方？",
        "工具回傳格式為什麼要統一？"
      ],
      "2-4": [
        "封裝 ReAct loop 後，哪裡負責決策、哪裡負責執行？",
        "max_steps 太大或太小會有什麼影響？",
        "如何防止 Agent 一直重複呼叫同一個工具？"
      ],
      "2-5": [
        "程式碼助理讀檔前為什麼通常要先 list/search？",
        "rg 搜尋比逐檔讀取好在哪？",
        "大型專案中應該如何限制讀檔範圍？"
      ],
      "2-6": [
        "unified diff 的 ---、+++、@@ 分別代表什麼？",
        "為什麼第一版只產生 patch，不直接改檔？",
        "審查 patch 時應該先看哪些風險？"
      ],
      "2-7": [
        "測試失敗輸出要怎麼定位真正錯誤？",
        "ZeroDivisionError 和 ValueError 差在哪？",
        "修 bug 前為什麼要先看測試期待？"
      ],
      "2-8": [
        "完整 CLI Agent 和單課範例的差別是什麼？",
        "我要怎麼讓這個 Agent 支援更多工具？",
        "如何把 CLI Agent 改成更安全的實用工具？"
      ],
      "3-1": [
        "好的 Prompt 通常包含哪些元素？",
        "結構化輸出為什麼能提高穩定性？",
        "要如何讓模型少講廢話、多做任務？"
      ],
      "3-2": [
        "路徑限制、命令白名單、禁止刪除各防什麼風險？",
        "什麼工具需要使用者確認才能執行？",
        "如果要開放寫檔，最少要加哪些保護？"
      ],
      "3-3": [
        "如何判斷 patch 是否改太多？",
        "patch 審查時測試要怎麼搭配？",
        "什麼情況應該拒絕 Agent 的修改？"
      ],
      "3-4": [
        "標準除錯流程為什麼是先測試再讀檔？",
        "如何把錯誤訊息轉成搜尋關鍵字？",
        "Agent 自主除錯和人類除錯如何分工？"
      ],
      "3-5": [
        "為什麼 exe 適合使用，不適合一開始學習？",
        "打包後還需要保留原始碼嗎？",
        "如何確認 exe 不是黑盒，而是教學入口？"
      ]
    };

    const generalHints = [
      "請用更簡單的比喻解釋剛剛的內容",
      "這一課最重要的三個觀念是什麼？",
      "我可以做哪個小練習確認自己懂了？"
    ];

    function setOutput(text, suggestions = []) {
      document.getElementById("output").textContent = text || "(沒有輸出)";
      showSuggestions(suggestions);
    }

    function showSuggestions(items) {
      const block = document.getElementById("suggestionBlock");
      const root = document.getElementById("suggestions");
      root.innerHTML = "";
      if (!items || items.length === 0) {
        block.style.display = "none";
        return;
      }
      for (const question of items.slice(0, 5)) {
        const button = document.createElement("button");
        button.className = "suggestion";
        button.textContent = question;
        button.onclick = () => askSuggested(question);
        root.appendChild(button);
      }
      block.style.display = "block";
    }

    function hintsForLesson(lesson) {
      if (!lesson) return generalHints;
      return lessonHints[lesson.code] || generalHints;
    }

    function hintsForAgent(prompt, output) {
      const text = `${prompt}\n${output}`;
      if (text.includes("Path not found") || text.includes("File not found")) {
        return [
          "為什麼 Agent 會找不到 workspace 路徑？",
          "請說明 safe_path 如何保護檔案讀取",
          "我要如何檢查目前 Agent 的工作目錄？"
        ];
      }
      if (text.includes("patch") || text.includes("diff") || text.includes("修正")) {
        return [
          "請把剛剛的修正整理成 unified diff",
          "這個 patch 有哪些風險需要審查？",
          "修完後應該跑哪些測試？"
        ];
      }
      if (text.includes("測試") || text.includes("ZeroDivisionError") || text.includes("unittest")) {
        return [
          "請解釋這個測試失敗的根本原因",
          "請提出最小修改的修正方向",
          "為什麼測試期待 ValueError 而不是 ZeroDivisionError？"
        ];
      }
      return [
        "請把剛剛的回答整理成學習筆記",
        "請給我一個可以立刻動手做的小練習",
        "下一步我應該學哪個 agent 概念？"
      ];
    }

    function askSuggested(question) {
      document.getElementById("agentPrompt").value = question;
      askAgent();
    }

    async function init() {
      const status = await api("/api/status");
      document.getElementById("status").textContent = `專案位置：${status.root}`;
      const data = await api("/api/lessons");
      lessons = data.lessons;
      renderLessons();
      selectLesson(lessons[0]);
    }

    function renderLessons() {
      const root = document.getElementById("lessons");
      root.innerHTML = "";
      for (const lesson of lessons) {
        const button = document.createElement("button");
        button.className = "lesson";
        button.dataset.script = lesson.script;
        button.onclick = () => selectLesson(lesson);
        button.innerHTML = `
          <div class="num">${lesson.number}</div>
          <div>
            <div class="lesson-title">[${lesson.code}] ${lesson.title}</div>
            <div class="lesson-summary">${lesson.summary}</div>
          </div>`;
        root.appendChild(button);
      }
    }

    function selectLesson(lesson) {
      selected = lesson;
      document.getElementById("lessonTitle").textContent = `[${lesson.code}] ${lesson.title}`;
      document.getElementById("lessonMeta").textContent = `${lesson.summary} ｜ ${lesson.script}`;
      for (const item of document.querySelectorAll(".lesson")) {
        item.classList.toggle("active", item.dataset.script === lesson.script);
      }
      showSuggestions(hintsForLesson(lesson));
    }

    function selectFirst() {
      selectLesson(lessons[0]);
      runSelectedLesson();
    }

    async function runSelectedLesson() {
      if (!selected) return;
      setOutput(`正在執行 ${selected.title}...\n`, []);
      const result = await api("/api/run-lesson", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({script: selected.script})
      });
      setOutput(result.output, hintsForLesson(selected));
    }

    async function runTests() {
      setOutput("正在執行測試...\n", []);
      const result = await api("/api/run-tests", {method: "POST"});
      setOutput(result.output, [
        "請解釋測試失敗中的關鍵錯誤訊息",
        "請根據測試輸出提出修正 patch",
        "修正前我應該先讀哪個檔案？"
      ]);
    }

    async function loadNote(name) {
      const result = await api(`/api/note/${name}`);
      setOutput(result.content, generalHints);
    }

    async function askAgent() {
      const prompt = document.getElementById("agentPrompt").value;
      setOutput("Agent 思考中，可能需要一點時間...\n", []);
      const result = await api("/api/agent", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({prompt})
      });
      setOutput(result.output, hintsForAgent(prompt, result.output));
    }

    async function openFolder() {
      const result = await api("/api/open-folder", {method: "POST"});
      setOutput(result.output, [
        "我應該先看哪些檔案理解這個專案？",
        "請說明 lessons、agent、workspace 三個資料夾的用途",
        "如何從原始碼對應到 UI 上的功能？"
      ]);
    }

    init();
  </script>
</body>
</html>
"""


def main() -> None:
    parser = argparse.ArgumentParser(description="Start the LocalAgentTutor web UI.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args()

    server = ThreadingHTTPServer((args.host, args.port), TutorHandler)
    url = f"http://{args.host}:{args.port}"
    print(f"LocalAgentTutor UI: {url}")
    print("按 Ctrl+C 停止。")
    if not args.no_browser:
        threading.Thread(target=lambda: (time.sleep(0.6), webbrowser.open(url)), daemon=True).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nUI 已停止。")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
