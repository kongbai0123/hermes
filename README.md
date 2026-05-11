# ⚡ Hermes Agent OS

> **A Cyberpunk-Themed Local AI Agent Operating System.**

Hermes 是一個致力於提供高度可觀測、受控且安全的本地 AI 代理作業系統。它不僅具備極致視覺美感的賽博龐克 (Cyberpunk) 儀表板，更核心的是其「唯讀 Runtime (Read-Only Runtime)」架構，確保 AI 代理在執行任務時始終處於人類的監督與預設的安全邊界內。

![Hermes UI Preview](https://raw.githubusercontent.com/kongbai0123/hermes/main/hermes/api/preview.png) *(註：此為範例路徑)*

---

## 🚀 核心特點 (Core Features)

- **Cyber-Codex Dashboard**: 深度定制的極致視覺介面，包含動態 Token 監控、終端機日誌流與精密參數控制。
- **Read-Only Runtime**: 基於 Harness Engineering 原則，優先實作安全唯讀工具調用，建立代理執行的誠信基礎。
- **Local-First (Ollama)**: 優先支援 Ollama 本地模型（如 Qwen3, Llama3），確保您的數據隱私不出站。
- **Interactive Tooltip System**: 全域賽博菱形提示系統，即時解釋所有 AI 參數與工具用途。
- **Scene Switcher**: 支援多種視覺場景切換（Cyber-Dark / Standard-Light），適應不同光線環境。

## 🛠️ 技術棧 (Tech Stack)

- **Frontend**: Vanilla HTML5, CSS3 (Modern Flex/Grid), JavaScript (ES6+).
- **Backend**: Python 3.10+ (Zero-dependency API server).
- **LLM**: Ollama API Integration.

## 📥 快速啟動 (Quick Start)

1. **環境準備**: 確保已安裝 Python 3.10+ 並啟動了 [Ollama](https://ollama.com/)。
2. **複製專案**:
   ```bash
   git clone https://github.com/kongbai0123/hermes.git
   cd hermes
   ```
3. **啟動系統**:
   直接執行根目錄下的 `RUN_HERMES.bat` 或在終端機執行：
   ```bash
   python start_hermes.py
   ```
4. **進入儀表板**: 打開瀏覽器訪問 `http://localhost:8000/dashboard.html`。

## 🗺️ 開發規劃 (Roadmap)

- [x] **V0.1**: 基礎 Cyberpunk UI 與 Ollama 整合。
- [x] **V0.2**: 實作使用者設定持久化與 Token 監控系統。
- [ ] **V0.3 (In Progress)**: 建立 Read-Only Runtime、SafeExecutor 與 Trace Timeline。
- [ ] **V0.4**: 實作多步驟任務規劃與自動化測試代理。
- [ ] **V0.5**: 開放受控的寫入權限與 PR 建議模式。

---

## 📜 許可證 (License)

MIT License. See `LICENSE` for more information.

---

**Developed with ⚡ by Antigravity AI.**
