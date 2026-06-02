# Work Agent

這是一個簡單、可實務使用的本機 agent 範例，用來學會四個核心角色：

| 名稱 | 作用 |
| --- | --- |
| Agent Loop | 管理流程 / 執行流程 |
| Manager Model | 管理者 / 決策角色 |
| Worker Models | 執行者 / 專業角色 |
| Tools | 工具能力 |

## Harness 觀念

這個專案採用輕量版的 Harness Engineering 思路：

- `AGENTS.md` 當地圖，不當大手冊
- `docs/` 當系統記錄依據
- 先觀察，再驗證，再提出建議
- 用安全邊界換取低錯誤率與高可用性

## 啟動方式

```powershell
cd G:\program\agent\work_agent
python -m simple_agent.main
```

或直接執行：

```powershell
run_agent.cmd
```

建議先閱讀：

- `AGENTS.md`
- `docs/architecture.md`
- `docs/workflow.md`
- `docs/quality.md`

## 可做的實務工作

- 分析 `workspace/` 裡的專案結構
- 搜尋程式碼與文字
- 讀取指定檔案
- 執行白名單命令，例如 `python --version`、`pytest`
- 讓 Manager Model 規劃任務
- 讓 Worker Model 根據工具結果整理回覆

## 指令範例

```text
請分析 workspace 的檔案結構
搜尋 calculator 這個關鍵字
讀取 README.md
執行 python --version
```

## 安全邊界

- 檔案工具只允許操作本資料夾的 `workspace/`
- 預設不寫入、不刪除檔案
- 命令工具只允許白名單命令
- 每次工具呼叫都會印出 Observation，方便學習 Agent Loop

## 對應關係

```text
使用者輸入
↓
Agent Loop 接收任務
↓
Manager Model 產生計畫與路由
↓
Worker Model 執行專業工作
↓
Tools 讀檔 / 搜尋 / 跑測試
↓
Observation 回到 Agent Loop
↓
Worker Model 整理答案
↓
回覆使用者
```
