# Hermes: 本機 AI Agent 與多智能體 DAG 工作區

本專案是一個完整且開箱即用的本機 AI Agent 開發、學習與測試生態系統。它結合了本機 LLM 呼叫、安全的工具沙箱（Sandboxed Tools）、互動式教學 UI，以及一個現代化的 Web 多智能體 DAG（有向無環圖）工作區。

---

## 📁 專案結構

此工作區包含以下三個主要模組：

### 1. [lesson](file:///G:/program/agent/lesson/README.md) - LocalAgentTutor 邊做邊學
- **目的**：帶領開發者一步步理解並手寫 Agent 的底層邏輯。
- **內容**：
  - **第一軌**：完全手寫的底層原理（Chat、Memory、ReAct 迴圈、File Tools）。
  - **第二軌**：模組化 Agent 架構（程式碼閱讀器、Patch 產生器、測試執行器、CLI 互動式介面）。
  - **第三軌**：實務技能（Prompt 設計、安全邊界、Patch 審查、EXE 打包）。
- **入口**：`lesson/dist/LocalAgentTutorUI.exe`（網頁介面）與 `lesson/dist/LocalAgentTutor.exe`（CLI 選單）。

### 2. [work_agent](file:///G:/program/agent/work_agent/README.md) - CLI 執行代理核心
- **目的**：執行具體任務的本機 CLI Agent 核心，支援實務開發工作（分析專案結構、程式碼搜尋、執行單元測試等）。
- **核心設計**：
  - **Manager Model**：負責整體規劃、任務路由。
  - **Worker Model**：負責專業執行與工具調用。
  - **安全防護**：僅允許存取 `workspace/` 資料夾，具備命令白名單限制，所有工具呼叫皆有 Observation 記錄。

### 3. [work_agent_web](file:///G:/program/agent/work_agent_web/README.md) - Web 代理工作區 (多智能體 DAG 平台)
- **目的**：React 19 + Tailwind + Express 打造的 Chat-first 智能體工作區，具備視覺化的 **閉環 Agent Flow / Team Canvas DAG**。
- **功能特色**：
  - **多智能體 DAG 編排**：支援動態層級排程（DAG Level Scheduling），可自定義 Planner、Coder、Reviewer、Verifier 等智能體節點。
  - **閉環驗證與自動回溯 (Backtracking)**：Verifier 節點自動對輸出評分。若未達標，將根據 Feedback 與 Backtracking 策略自動回溯至特定節點重新生成，提供自我修正（Self-Correction）能力。
  - **工作區整合**：支援即時檢視本機專案樹（Project Tree Viewer）、檔案內容與 Patch 套用。
  - **意圖分類 (Task Intent)**：自動解析使用者提示詞意圖以最佳化執行路徑。

---

## 🚀 快速啟動

### 方式 A：啟動網頁智能體工作區（推薦）
在專案根目錄下直接執行：
```powershell
.\open_work_agent_web.cmd
```
此腳本會自動完成編譯、啟動 Express 後端與 React 前端伺服器，並開啟瀏覽器存取 `http://localhost:3000`。

### 方式 B：啟動 CLI Agent 進行命令行對話
進入 `work_agent` 目錄並啟動：
```powershell
cd G:\program\agent\work_agent
.\run_agent.cmd
```

### 方式 C：開啟 LocalAgentTutor 學習入口
直接雙擊執行：
```powershell
G:\program\agent\lesson\dist\LocalAgentTutorUI.exe
```

---

## 🛠️ 開發與設定

- **模型配置**：本專案預設使用本機 [Ollama](https://ollama.com/) 作為模型供應商，建議下載 `gemma4:latest` 或 `qwen-local:latest`。
- **環境變數**：
  - Web 伺服器預設埠為 `3000`。
  - 可利用 `WORK_AGENT_PYTHON` 指定 Python 執行路徑。
