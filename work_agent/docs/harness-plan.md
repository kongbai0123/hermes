# Lightweight Harness Plan

## Goal

根據 OpenAI 的 Harness Engineering 文章，為 Work Agent 建立一個不複雜、但實用且可持續的本機 harness。

## Design Principles

### 1. 地圖比手冊重要

`AGENTS.md` 保持精簡，只負責導航。更細的規則寫進 `docs/`。

### 2. 工具優先於長 prompt

能靠工具驗證的事情，就不要只靠模型猜。

### 3. 固定流程優先於自由發揮

先觀察、再整理、再驗證、最後建議。

### 4. 限制是加速器

白名單命令、限定 workspace、拒絕危險操作，能降低錯誤率，讓使用者更敢用。

## Practical Roadmap

### Phase 1

- 建立 `AGENTS.md`
- 建立 `docs/`
- 對齊 README、工具規則、品質規則

### Phase 2

- 增加 `write_patch` 或 patch 草案輸出
- 增加常見任務範本
- 讓 `run_command` 對測試失敗做更好摘要

### Phase 3

- 把常見流程包成捷徑命令
- 增加更清楚的審查與驗收輸出
- 視需要再導入更進一步的 UI 或 MCP

## Why This Is Enough For Now

這個版本的目的不是模仿大型內部平台，而是先做出一個：

- 容易理解
- 容易維護
- 容易驗證
- 真的能幫你加快開發

