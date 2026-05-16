# ⚡ Hermes Agent OS

> **A Cyberpunk-Themed Local AI Agent Operating System.**

Hermes 是一個致力於提供高度可觀測、受控且安全的本地 AI 代理作業系統。它不僅具備極致視覺美感的賽博龐克 (Cyberpunk) 儀表板，更核心的是其「唯讀 Runtime (Read-Only Runtime)」架構，確保 AI 代理在執行任務時始終處於人類的監督與預設的安全邊界內。

![Hermes UI Preview](https://raw.githubusercontent.com/kongbai0123/hermes/main/hermes/api/preview.png) *(註：此為範例路徑)*

---

## 🚀 核心特點 (Core Features)

- **Cyber-Codex Dashboard**: 深度定制的極致視覺介面，包含動態 Token 監控、終端機日誌流與精密參數控制。
- **Controlled Autonomous Runtime (V0.4-pre)**: 具備治理閘門的自主循環核心，支援 Observe-Plan-Execute 閉環任務。
- **Governance Layer**: 內置 `GovernanceManager` 與 `SafeExecutor`，所有高風險操作（寫入、Shell）均需雙重授權。
- **Management Decision Layer**: 展示 Executive、Strategy、Operator、Auditor 四層管理鏈，實現 AI 決策透明化。
- **Local-First (Ollama)**: 支援 Ollama 本地模型（如 Qwen2.5/3），確保您的數據隱私不出站。

## 🛠️ 技術棧 (Tech Stack)

- **Frontend**: Vanilla HTML5, CSS3, JavaScript (ES6+).
- **Backend**: Python 3.12 (Zero-dependency custom HTTP server).
- **LLM**: Ollama API Integration.

## 📥 快速啟動 (Quick Start)

1. **環境準備**: 確保已安裝 Python 3.12 並啟動了 [Ollama](https://ollama.com/)。
2. **複製專案**:
   ```bash
   git clone https://github.com/kongbai0123/hermes.git
   cd hermes
   ```
3. **啟動系統**:
   直接執行根目錄下的 `RUN_HERMES.bat`。它會自動啟動後端並開啟瀏覽器。
4. **進入儀表板**: 訪問 `http://localhost:8000/dashboard.html`。

---

## 🗺️ 專案進度與里程碑 (Status & Roadmap)

### 目前狀態：V0.4-pre (Controlled Autonomous Runtime Kernel)
Hermes 目前已具備穩定的本地代理運作核心，支援以下能力：
- **自主循環**: 可進行多輪工具觀察與回饋，具備 `max_iterations` 截斷防止無限循環。
- **治理診斷面板**: 右側 DECISION 面板可顯示 L1-L4 的即時治理鏈狀態與執行風險。
- **受控寫入流程**: 已實作 `propose_patch` 與審核 API，寫入操作需經過 User Approval 與 Governance Gate。
- **高覆蓋率測試**: 143+ 行為測試確保安全邊界穩固。

### V0.5 規劃：產品級治理體驗 (In Progress)
- [ ] **審核流程產品化**: 完善 Patch 與 Shell 的審核 UI/API 閉環。
- [ ] **Scoped 權限授權**: 從全域權限轉向基於任務/時間的臨時授權。
- [ ] **Trace Schema 標準化**: 穩定診斷資料格式，提升可觀測性。
- [ ] **README / Demo 補完**: 提供完整的安裝指南與 Demo 任務說明。

---

## 📜 許可證 (License)
MIT License. Developed with ⚡ by Antigravity AI.
