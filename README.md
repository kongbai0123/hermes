# ⚡ Hermes Agent OS
[![Hermes Governance CI](https://github.com/kongbai0123/hermes/actions/workflows/test.yml/badge.svg)](https://github.com/kongbai0123/hermes/actions/workflows/test.yml)

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
- **Model Context Protocol (MCP)**: 提供標準化的 MCP Server 入口，支持與 Claude Code、Cursor 等客戶端深度集成。[查看 MCP 指南](docs/mcp.md)

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
   - **本機啟動**: 直接執行根目錄下的 `RUN_HERMES.bat`。它會自動啟動後端並開啟瀏覽器。
   - **沙盒安全啟動 (Docker)**: 一鍵建立完全物理隔離的 L5 自治環境：
     ```bash
     docker-compose up -d --build
     ```
4. **進入儀表板**: 訪問 `http://localhost:8000/dashboard.html`。[查看沙盒架構與安全細節](docs/docker_sandbox.md)

---

## 🗺️ 專案進度與里程碑 (Status & Roadmap)

### V0.5 規劃：產品級治理體驗 (In Progress)
- [x] **Autonomy Policy (L0-L5)**: 建立明確的權限分層，嚴格禁止 Markdown 繞過底層防護。
- [x] **Phase 6: Validation Suite**: 完成 `safety_validation_suite.json`，提供資料驅動的安全邊界白箱/黑箱自動化測試。
- [x] **Phase 3: Tool Failure Backoff**: 實作連續錯誤退避機制（暫停並請求人工介入），防止 Agent 暴走，具備強大的 Fail-safe 能力。
- [x] **Phase 4: Docker Sandbox**: 導入實體與邏輯雙層防禦（Defense in Depth），透過 non-root user 與資源限制打造安全的 L5 實驗環境。[查看沙盒詳細架構](docs/docker_sandbox.md)
- [ ] **Phase 5: Skill Curator (Next)**: 實作基於 Trace 與 Proposal-only 的自我進化學習機制。

---

## 📜 許可證 (License)
MIT License. Developed with ⚡ by Antigravity AI.
