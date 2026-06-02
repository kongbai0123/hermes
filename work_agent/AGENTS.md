# Work Agent Map

這份 `AGENTS.md` 是 Work Agent 的地圖，不是百科全書。

## Goal

把這個專案維持成一個輕量、實用、低錯誤率的本機開發 agent，重點是：

- 能快速理解 `workspace/`
- 能安全地讀檔、搜尋、跑白名單命令
- 能把結果整理成開發者可直接採用的建議
- 優先提升開發速度與可重現性，而不是追求花俏功能

## System Of Record

請優先閱讀這些檔案，而不是把所有規則塞進 prompt：

- `README.md`：快速使用方式
- `docs/architecture.md`：系統結構與角色分工
- `docs/workflow.md`：固定工作流程
- `docs/commands.md`：允許命令與工具使用方式
- `docs/quality.md`：品質規則與驗收標準
- `docs/harness-plan.md`：輕量版 harness 的實作路線

## Current Architecture

- `simple_agent/main.py`：CLI 入口
- `simple_agent/loop.py`：Agent Loop
- `simple_agent/roles.py`：Manager Model / Worker Models
- `simple_agent/tools.py`：檔案與命令工具
- `workspace/`：唯一允許的工作區
- `tests/`：目前的自動測試

## Working Rules

- 只操作 `workspace/` 內檔案
- 不直接刪除檔案
- 優先先觀察，再提出修改建議
- 若需要修改程式，先描述理由、風險與驗證方式
- 若任務可由工具驗證，預設要跑驗證
- 若文件與行為不一致，先更新文件或程式，避免漂移

## Default Task Loop

1. 先判斷任務是分析、搜尋、讀檔、測試還是解釋。
2. 只選必要的工具，不做多餘步驟。
3. 回傳 observation 時保留可讀性。
4. 回覆時至少包含：
   - 結果摘要
   - 下一步建議
   - 若有風險，直接指出

## Non-Goals For V1

- 不做多 agent 編排
- 不做複雜 MCP 依賴
- 不做自動改檔與自動提交
- 不做大型可觀測性平台

