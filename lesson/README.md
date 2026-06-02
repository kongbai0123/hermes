# LocalAgentTutor：本機 Codex-like Agent 邊做邊學

這是一套用 Python + Ollama + `gemma4:latest` 製作的本機 AI agent 教學專案。

目標不是只做一個黑盒工具，而是讓你邊執行、邊看程式、邊理解 agent 如何做到：

- 呼叫本機模型
- 保留對話記憶
- 使用工具
- 讀取與搜尋程式碼
- 分析測試錯誤
- 產生 patch
- 用安全限制避免誤操作
- 最後用 `LocalAgentTutor.exe` 當學習入口

## 快速開始

推薦直接啟動教學式 UI：

```powershell
G:\program\agent\lesson\dist\LocalAgentTutorUI.exe
```

也可以使用選單式啟動器：

```powershell
G:\program\agent\lesson\dist\LocalAgentTutor.exe
```

開發者模式才需要直接執行原始碼：

```powershell
cd G:\program\agent\lesson
python LocalAgentTutor.py
```

## LocalAgentTutor 選單

```text
LocalAgentTutor.exe
├─ 開始教學
│  ├─ 第一軌：底層原理手寫
│  ├─ 第二軌：模組化 Agent 架構
│  └─ 第三軌：Prompt、安全、Patch、除錯、打包
├─ 啟動 Agent
├─ 執行測試
├─ 查看筆記
├─ 開啟原始碼資料夾
├─ 檢查 Ollama 模型
└─ 開啟教學 UI
```

## 教學式 UI

`LocalAgentTutorUI.exe` 會在本機啟動瀏覽器介面，預設網址是：

```text
http://127.0.0.1:8765
```

UI 可以直接：

- 點選課程並執行
- 查看課程筆記
- 執行 sample project 測試
- 快速向本機 agent 提問
- 開啟原始碼資料夾
- 在課程或 Agent 回覆後顯示下一步可探索的延伸問題

一般使用者只需要開 `dist\LocalAgentTutorUI.exe`。原始碼保留在資料夾中，是為了學習與修改，不需要手動輸入 `py` 或 `python` 才能使用 UI。

## 課程路線

### 第一軌：底層原理手寫

位置：`lessons/part1_raw_basics/`

這一軌完全手寫，讓你理解 agent 最底層原理。

- `01_chat.py`：呼叫 Ollama 模型
- `02_chat_with_memory.py`：對話記憶
- `03_tools.py`：工具呼叫
- `04_react_agent.py`：ReAct 循環
- `05_file_agent.py`：檔案助理

### 第二軌：模組化架構

位置：`lessons/part2_modular_framework/`

這一軌使用 `agent/` 模組，學習如何把 agent 寫成可維護專案。

- `01_ollama_chat.py`：封裝模型呼叫
- `02_chat_memory.py`：封裝記憶
- `03_tools_basic.py`：工具註冊
- `04_react_loop.py`：ReAct 引擎
- `05_code_reader.py`：讀取與搜尋程式碼
- `06_patch_writer.py`：產生 patch
- `07_test_runner.py`：測試與驗證
- `08_agent_cli.py`：完整 CLI agent

### 第三軌：實用技能

位置：`lessons/part3_practical_skills/`

這一軌補上真正要用 agent 寫程式時會遇到的能力。

- `01_prompt_design.py`：Prompt 設計
- `02_safety_boundaries.py`：安全邊界
- `03_patch_review.py`：Patch 審查
- `04_debug_workflow.py`：除錯流程
- `05_packaging_exe.py`：打包 EXE 的正確觀念

## 啟動正式 Agent

```powershell
python agent/main.py
```

可嘗試輸入：

```text
請分析 workspace 裡的程式結構
找出 sample_project 的測試失敗原因
請提出修正 divide by zero 的 patch
```

## 打包成 EXE

```powershell
cd G:\program\agent\lesson
.\build_exe.ps1
```

輸出位置：

```text
dist\LocalAgentTutor.exe
```

## 安全規則

- 預設只讀取 `workspace/` 內檔案
- 不提供刪除工具
- 修改只產生 patch，不直接套用
- 命令執行使用白名單
- 工具呼叫會印在終端機，方便觀察 agent 的決策
