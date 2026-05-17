# ⚡ Hermes Docker Sandbox Architecture (沙盒隔離架構)

本文件說明 Hermes 系統的 Docker 沙盒架構。沙盒是 Hermes 達到 L5 Sandbox Autonomous 等級的核心基礎，提供了實體層級的安全隔離。

## 1. 核心設計理念：雙層防禦 (Defense in Depth)

Hermes 的安全架構由兩層組成，缺一不可：

* **邏輯層 (Python GovernanceManager)**: 決定 Hermes 允許做什麼 (例如阻擋寫入 `AUTO_APPROVE.md`)。
* **實體層 (Docker Sandbox)**: 限制 Hermes 做壞事時的破壞半徑 (無法逃逸至宿主機)。

> [!WARNING]
> **絕對禁止**：不要因為使用了 Docker 就將 `GovernanceManager` 的檢查關閉（例如 `return True`）。Docker 是用來防止「未知的逃逸」，而不是用來取代「已知的治理」。

## 2. 儲存與掛載策略 (Volume Mounts)

為了貫徹 Persistence Model，我們僅掛載特定的目錄，並施加嚴格的讀寫權限：

* `./user_projects:/workspace/user_projects` (Read/Write): 允許 Agent 生成靜態網站與專案。
* `./docs:/workspace/docs` (Read/Write): 允許 Agent 更新文檔與提出 Proposal。
* `./tests/fixtures:/workspace/tests/fixtures:ro` (Read-only): 測試規範絕對不允許 Agent 在運行中修改。

## 3. Ollama 宿主機連線

Hermes 運行於容器內，而 Ollama 模型通常運行於宿主機 (Host)。 透過設定環境變數 `HERMES_OLLAMA_BASE_URL=http://host.docker.internal:11434`，以及在 docker-compose 中設定 `extra_hosts`，Hermes 可以安全地呼叫宿主機的推論能力，而無需將巨大的模型打包進 Image。

## 4. 資源限制與安全性 (Resource Limits)

為防止模型生成的腳本（如無限迴圈、Fork Bomb）癱瘓系統，`docker-compose.yml` 中強制設定了資源上限：

* **CPU**: 最高 2.0 Cores
* **Memory**: 最高 2GB
* **User**: 強制使用非 root 的 `hermes` (UID 1000) 帳號執行所有程序。

## 5. L5 實驗室啟動指南

要啟動 L5 沙盒環境進行測試，請執行：
```bash
docker-compose up --build
```
此環境中的 Hermes 擁有最高自治度，但其破壞力已被限制在 `/workspace` 容器內。
