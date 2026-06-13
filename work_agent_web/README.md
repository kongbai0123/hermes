# Hermes Web Workbench (多智能體 DAG 平台)

本專案是 Hermes 智能體生態系統的 Web 前端與後端工作區。它提供了一個 Chat-first 的互動式介面，支援多智能體團隊畫布 (Agent Team Canvas)、閉環 DAG 流程視覺化、自動化驗證與回溯 (Verifier & Backtracking) 以及本機工作區瀏覽器。

---

## ✨ 核心功能

1. **視覺化 Agent Team Canvas (DAG)**
   - 支援將多個專業智能體節點（Planner, Coder, Reviewer, Verifier 等）組合成有向無環圖 (DAG)。
   - 提供動態層級拓撲排程（DAG Level Topology Scheduling），使無相依性的節點能並行執行，有相依性的節點按順序傳遞脈絡。

2. **閉環驗證與自動回溯 (Self-Correction & Backtracking)**
   - 內建 **Verifier** 節點，可對最終或階段性產出進行自動化品質評估。
   - 若評分低於門檻，將根據回溯策略（Backtracking Policy）攜帶反饋（Feedback）回溯至指定節點（如 Coder），實現自我修正閉環。

3. **實時串流與工作區互動 (Streaming & Workspace Explorer)**
   - 支援 SSE (Server-Sent Events) 的 NDJSON 串流格式，實時顯示各個節點的執行進度、思考過程與產出。
   - 左側內建本機工作區檔案瀏覽器，可直接查看代碼並套用智能體產生的修補程式 (Patch)。

4. **意圖分類與提示詞調優 (Task Intent & Prompt Optimization)**
   - 自動將使用者輸入的任務分類（如程式碼修改、效能優化、測試撰寫等），並為每個智能體節點動態生成最適合的 System/User Prompt。

5. **自動休眠機制 (Heartbeat Auto-Shutdown)**
   - 具備 7 秒心跳偵測（Heartbeat）。當網頁關閉且無活動請求時，後端伺服器將自動安全結束進程，避免浪費本機運算資源。

---

## 📁 檔案結構說明

```
client/
  src/
    components/
      AgentFlowPanel.tsx  ← 核心：DAG 視覺化面板與節點狀態渲染
      AppShell.tsx        ← 主畫面佈局與各面板排版
      ChatSidebar.tsx     ← 歷史對話列表管理
      ChatWindow.tsx      ← 對話視窗與串流輸出顯示
      RightPanel.tsx      ← 右側面板（整合 DAG 流程圖與推薦項目）
      ui/                 ← 基礎 UI 組件 (shadcn/ui & Radix)
    contexts/
      ChatContext.tsx     ← 管理對話、串流狀態與 API 交互
      LanguageContext.tsx ← 支援多國語言切換
      ThemeContext.tsx    ← 支援深色/淺色主題變更
server/
  index.ts                ← Express 伺服器，負責 DAG 拓撲計算、任務執行與 API 路由
shared/
  const.ts                ← 共用常數定義
```

---

## 🚦 後端 API 接口

Express 伺服器提供了以下 API 端點（位於 `server/index.ts`）：

- **`/api/heartbeat` (POST)**: 接收來自客戶端的心跳信號。
- **`/api/chat-state` (GET/PUT)**: 讀取或持久化對話歷史狀態至 `data/chat-state.json`。
- **`/api/workspace/tree` (GET)**: 列出本機 `work_agent/workspace/` 下的所有檔案與資料夾結構。
- **`/api/workspace/file` (GET)**: 讀取指定工作區檔案的源碼。
- **`/api/work-agent/run-stream` (POST)**: 單一智能體任務的實時串流接口。
- **`/api/work-agent/run-graph-stream` (POST)**: 執行多智能體 DAG 圖的拓撲流式執行接口，包含意圖分類與回溯驗證。
- **`/api/work-agent/patch` (POST)**: 調用 Agent 針對特定檔案生成 Patch。
- **`/api/work-agent/apply-patch` (POST)**: 將修補後的內容直接寫入本機工作區。

---

## 🚀 啟動與開發

請確保本機已安裝 [Ollama](https://ollama.com/) 且已下載對應模型（例如 `gemma4:latest` 或 `qwen-local:latest`）。

### 開發模式
1. 進入 `work_agent_web` 目錄：
   ```bash
   cd work_agent_web
   ```
2. 安裝依賴項：
   ```bash
   npm install
   ```
3. 啟動開發伺服器（同時啟動前端 Vite 與後端 Express 代理）：
   ```bash
   npm run dev
   ```

### 生產/打包模式
在專案根目錄下直接點擊 `open_work_agent_web.cmd` 即可自動完成打包與部署啟動。
