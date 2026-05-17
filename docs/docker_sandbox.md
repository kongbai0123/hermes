# ⚡ Hermes Docker Sandbox Architecture (沙盒隔離架構)

本文件定義 Hermes 的 L5 (Sandbox Autonomous) 實體物理隔離邊界。透過 Docker 容器化技術，將 AI 代理的執行環境完全限制在沙盒邊界內，實現主機免受惡意代碼或誤操作影響的終極防禦。

## 🪐 隔離架構 (Isolation Architecture)

```text
+-------------------------------------------------------------+
|                      Host Machine                           |
|  +------------------+                   +----------------+  |
|  |   Ollama LLM     |                   |  user_projects |  |
|  |  (Port 11434)    |                   |    (Volume)    |  |
|  +--------^---------+                   +--------^-------+  |
+-----------|--------------------------------------|----------+
            | host.docker.internal                 | Volume Mount
+-----------|--------------------------------------|----------+
|  +--------v---------+                   +--------v-------+  |
|  |  Hermes Server   |                   |  /app/projects |  |
|  |   (Port 8000)    |                   |   Workspace    |  |
|  +------------------+                   +----------------+  |
|                                                             |
|                Hermes Docker Sandbox Container              |
|                      (Non-root: hermes)                     |
+-------------------------------------------------------------+
```

### 1. 最小特權原則 (Least Privilege)
* **Non-root 執行**：容器內部強制使用 `UID 1000` 的 `hermes` 使用者運行，嚴禁以系統管理員（root）身分執行，切斷容器逃逸的可能性。
* **禁用權限提升 (no-new-privileges)**：在 `docker-compose.yml` 中加入了 `security_opt: ["no-new-privileges:true"]` 安全選項，防止任何通過 setuid 或 setgid 二進位檔案取得 root 權限的嘗試。

### 2. 網路邊界 (Network Boundary)
* **主機通訊橋接**：通過 `host.docker.internal` 與主機上的 Ollama (Port 11434) 或其他本地 API 服務通訊。
* **單向入口暴露**：容器僅向外暴露 `8000` 連接埠（用於 Web Dashboard 與 API 接口），容器內部代理無法直接掃描或控制主機的本機通訊。

### 3. 持久化邊界 (Persistence Boundary)
* **路徑隔離**：透過 Docker Volume Mount 將主機的 `./user_projects` 與 `./scratch` 掛載到容器的 `/app/user_projects` 和 `/app/scratch`。
* **唯讀核心保護**：Hermes 核心原始碼 (`hermes/`) 在容器內被視為唯讀，任何嘗試直接寫入的行為都會因路徑校驗與非 root 權限而被安全阻擋。

---

## 🚀 快速啟動沙盒環境 (Quick Start)

### 1. 建置與啟動
在專案根目錄下，直接使用以下指令一鍵建置並在背景運行：
```bash
docker-compose up -d --build
```

### 2. 查看運行日誌
```bash
docker logs -f hermes_sandbox
```

### 3. 開啟網頁工作台
造訪 `http://localhost:8000/dashboard.html`，即可進入賽博龐克風格的安全治理工作台。

---

## 🗺️ 治理對照表 (Autonomy Level Mapping)

當 Hermes 運行於 Docker Sandbox 時，各自治等級的安全限制與處理如下：

| 自治等級 | 物理限制 (Docker) | 治理閘門 (GovernanceManager) | 預期結果 |
|---|---|---|---|
| **L0 (Read-only)** | 無法修改容器外檔案 | 唯讀攔截，禁止寫入 | `allowed` (讀取) / `rejected` (寫入) |
| **L2 (Scoped Write)** | Volume Mount 持久化 | 強制路徑位於 `/app/user_projects/` | `allowed` (範圍內) / `rejected` (範圍外) |
| **L4 (Governed Shell)** | 指令受限於容器內部，無主機權限 | 僅能執行容器內安裝之指令 (git, curl) | `allowed` (白名單) / `rejected` (高危) |
| **L5 (Sandbox Autonomous)**| 物理邊界全面防護，主機免於逃逸威脅 | 容器內部全權授權執行，無需反覆阻擋 | **物理防護，高自治暢行** |

---

> [!IMPORTANT]
> **安全運維聲明**：
> 雖然 Docker 提供了極高的隔離性，但請確保您的 Docker 守護行程（Docker Daemon）保持最新版本，且不要掛載敏感的系統目錄（如 `/var/run/docker.sock`）到容器內部。
