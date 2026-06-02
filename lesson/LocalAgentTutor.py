"""Interactive learning launcher for the local agent tutorial."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


ROOT = None
PYTHON_CMD = None


LESSONS = [
    (
        "1-1",
        "底層原理：呼叫模型",
        "lessons/part1_raw_basics/01_chat.py",
        "看見最原始的 Ollama HTTP 呼叫與串流輸出。",
    ),
    (
        "1-2",
        "底層原理：對話記憶",
        "lessons/part1_raw_basics/02_chat_with_memory.py",
        "理解 LLM 不會自動記住對話，記憶是由程式餵回 prompt。",
    ),
    (
        "1-3",
        "底層原理：工具呼叫",
        "lessons/part1_raw_basics/03_tools.py",
        "學會讓模型輸出 JSON，再由 Python 執行工具。",
    ),
    (
        "1-4",
        "底層原理：ReAct Agent",
        "lessons/part1_raw_basics/04_react_agent.py",
        "理解 Thought、Action、Observation、Final Answer 的循環。",
    ),
    (
        "1-5",
        "底層原理：檔案助理",
        "lessons/part1_raw_basics/05_file_agent.py",
        "把工具接到本機檔案，學習安全邊界。",
    ),
    (
        "2-1",
        "模組化：模型連線",
        "lessons/part2_modular_framework/01_ollama_chat.py",
        "把模型呼叫封裝成 agent.llm.generate。",
    ),
    (
        "2-2",
        "模組化：記憶管理",
        "lessons/part2_modular_framework/02_chat_memory.py",
        "用 ConversationMemory 管理上下文。",
    ),
    (
        "2-3",
        "模組化：工具註冊",
        "lessons/part2_modular_framework/03_tools_basic.py",
        "理解工具 registry 與統一 observation 格式。",
    ),
    (
        "2-4",
        "模組化：ReAct Loop",
        "lessons/part2_modular_framework/04_react_loop.py",
        "把多步推理封裝成可重用引擎。",
    ),
    (
        "2-5",
        "程式助理：讀取與搜尋程式碼",
        "lessons/part2_modular_framework/05_code_reader.py",
        "學會讓 agent 找檔案、讀程式、定位線索。",
    ),
    (
        "2-6",
        "程式助理：產生 Patch",
        "lessons/part2_modular_framework/06_patch_writer.py",
        "學會先產生 diff，不直接改檔。",
    ),
    (
        "2-7",
        "程式助理：測試與驗證",
        "lessons/part2_modular_framework/07_test_runner.py",
        "讓 agent 看測試失敗輸出，推論修正方向。",
    ),
    (
        "2-8",
        "完整 CLI Agent",
        "lessons/part2_modular_framework/08_agent_cli.py",
        "啟動可互動的本機 Codex-like agent。",
    ),
    (
        "3-1",
        "進階：Prompt 設計",
        "lessons/part3_practical_skills/01_prompt_design.py",
        "比較鬆散 prompt 與結構化 prompt 的差異。",
    ),
    (
        "3-2",
        "進階：安全邊界",
        "lessons/part3_practical_skills/02_safety_boundaries.py",
        "驗證路徑限制、命令白名單與禁止破壞性操作。",
    ),
    (
        "3-3",
        "進階：Patch 審查",
        "lessons/part3_practical_skills/03_patch_review.py",
        "學會人工審查 agent 產生的修改提案。",
    ),
    (
        "3-4",
        "進階：除錯工作流",
        "lessons/part3_practical_skills/04_debug_workflow.py",
        "把讀檔、測試、錯誤解釋、patch 串成流程。",
    ),
    (
        "3-5",
        "進階：打包觀念",
        "lessons/part3_practical_skills/05_packaging_exe.py",
        "理解 .py 學習模式與 .exe 啟動器各自用途。",
    ),
]


def main() -> None:
    global ROOT, PYTHON_CMD
    ROOT = find_project_root()
    PYTHON_CMD = find_python_command()
    while True:
        clear()
        print_header()
        print("1. 開始教學")
        print("2. 啟動 Agent")
        print("3. 執行測試")
        print("4. 查看筆記")
        print("5. 開啟原始碼資料夾")
        print("6. 檢查 Ollama 模型")
        print("7. 開啟教學 UI")
        print("0. 離開")
        choice = read_input("\n請選擇> ", default="0")

        if choice == "1":
            lesson_menu()
        elif choice == "2":
            run_python("agent/main.py")
        elif choice == "3":
            run_tests()
        elif choice == "4":
            notes_menu()
        elif choice == "5":
            open_source_folder()
        elif choice == "6":
            run_command(["ollama", "list"], pause=True)
        elif choice == "7":
            open_tutor_ui()
        elif choice == "0":
            print("Bye.")
            return
        else:
            pause("無效選項。")


def lesson_menu() -> None:
    while True:
        clear()
        print_header("開始教學")
        for index, (lesson_id, title, _, summary) in enumerate(LESSONS, start=1):
            print(f"{index:>2}. [{lesson_id}] {title} - {summary}")
        print(" 0. 返回主選單")
        choice = read_input("\n請選擇課程編號> ", default="0")
        if choice == "0":
            return

        lesson = find_lesson(choice)
        if lesson is None:
            pause("找不到這個課程。請輸入左側數字，例如 1，或課程代碼，例如 1-1。")
            continue
        _, title, script, summary = lesson
        clear()
        print_header(title)
        print(summary)
        print(f"\n執行檔案：{script}\n")
        run_python(script)


def find_lesson(choice: str) -> tuple[str, str, str, str] | None:
    normalized = choice.strip().lower()
    if normalized.isdigit():
        index = int(normalized)
        if 1 <= index <= len(LESSONS):
            return LESSONS[index - 1]
    return next((item for item in LESSONS if item[0].lower() == normalized), None)


def notes_menu() -> None:
    while True:
        clear()
        print_header("查看筆記")
        print("1. 課程總覽 README")
        print("2. Lessons Guide")
        print("3. 學習筆記")
        print("4. 實戰工作流")
        print("5. 打包 EXE 說明")
        print("0. 返回主選單")
        choice = read_input("\n請選擇> ", default="0")
        files = {
            "1": ROOT / "README.md",
            "2": ROOT / "lessons" / "README.md",
            "3": ROOT / "notes" / "LESSONS.md",
            "4": ROOT / "notes" / "WORKFLOWS.md",
            "5": ROOT / "notes" / "PACKAGING.md",
        }
        if choice == "0":
            return
        path = files.get(choice)
        if path is None:
            pause("無效選項。")
            continue
        show_file(path)


def run_tests() -> None:
    clear()
    print_header("執行測試")
    print("這個測試會故意失敗一次，目的是讓你練習 agent 查錯與產生 patch。\n")
    run_command(PYTHON_CMD + ["-m", "unittest", "discover", "-s", "workspace/sample_project"], pause=True)


def run_python(script: str) -> None:
    run_command(PYTHON_CMD + [str(ROOT / script)], pause=True)


def open_tutor_ui() -> None:
    ui_exe = ROOT / "dist" / "LocalAgentTutorUI.exe"
    if getattr(sys, "frozen", False):
        sibling_ui_exe = Path(sys.executable).resolve().with_name("LocalAgentTutorUI.exe")
        if sibling_ui_exe.exists():
            ui_exe = sibling_ui_exe
    if ui_exe.exists():
        subprocess.Popen([str(ui_exe)], cwd=ROOT)
        pause("已啟動教學 UI。瀏覽器會自動開啟。")
        return
    run_python("tutor_ui.py")


def run_command(command: list[str], *, pause: bool = False) -> int:
    sys.stdout.flush()
    try:
        completed = subprocess.run(command, cwd=ROOT, check=False)
        code = completed.returncode
    except FileNotFoundError:
        print(f"找不到命令：{command[0]}")
        code = 127
    if pause:
        read_input(f"\n結束代碼：{code}。按 Enter 返回...")
    return code


def show_file(path: Path) -> None:
    clear()
    print_header(path.name)
    if not path.exists():
        print(f"找不到檔案：{path}")
    else:
        print(path.read_text(encoding="utf-8", errors="replace"))
    read_input("\n按 Enter 返回...")


def open_source_folder() -> None:
    os.startfile(ROOT)
    pause(f"已開啟：{ROOT}")


def print_header(title: str = "LocalAgentTutor") -> None:
    print("=" * 72)
    print(title)
    print("=" * 72)
    print(f"專案位置：{ROOT}")
    print()


def clear() -> None:
    os.system("cls")


def pause(message: str) -> None:
    read_input(f"{message}\n按 Enter 繼續...")


def read_input(prompt: str, *, default: str = "") -> str:
    try:
        return input(prompt).strip()
    except EOFError:
        return default


def find_project_root() -> Path:
    """Find the tutorial folder when running as .py or as dist/*.exe."""

    candidates = [
        Path.cwd(),
        Path(__file__).resolve().parent,
        Path(sys.executable).resolve().parent,
        Path(sys.executable).resolve().parent.parent,
    ]
    for candidate in candidates:
        if (candidate / "lessons").is_dir() and (candidate / "agent").is_dir():
            return candidate
    return Path.cwd()


def find_python_command() -> list[str]:
    if not getattr(sys, "frozen", False):
        return [sys.executable]
    candidates = [
        ["py", "-3.12"],
        ["py", "-3.11"],
        ["python"],
    ]
    for candidate in candidates:
        try:
            completed = subprocess.run(
                candidate + ["--version"],
                cwd=ROOT,
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
        except (FileNotFoundError, subprocess.TimeoutExpired):
            continue
        if completed.returncode == 0:
            return candidate
    return ["python"]


if __name__ == "__main__":
    main()
