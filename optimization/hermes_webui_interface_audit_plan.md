# Hermes Workbench UI Audit and Layout Strategy

建立日期：2026-05-13

## 1. 決策摘要

本次依據 `https://github.com/nesquena/hermes-webui` 的 WebUI 思路，檢查 Hermes 本地 Dashboard 後，建議採用：

```text
Three-panel professional workbench
+ reply-first execution surface
+ right-side workspace / decision / tools inspector
+ strict API contract parity across FastAPI and lightweight server
+ no-build Python + Vanilla JS, but modularized static assets
```

目前本地介面已朝三欄式 Workbench 前進，但仍存在幾個全端工程缺口：

1. `dashboard.html` 呼叫 `/api/files/list` 與 `/api/files/read`，但 `start_hermes.py` 沒有這兩個 endpoint。
2. `hermes/api/server.py` 有 `/api/files/list`，但缺 `/api/files/read`。
3. 右側 Files tab 的失敗訊息過於籠統，沒有顯示 HTTP status、錯誤原因或修復建議。
4. Dashboard 仍是單一大型 HTML，CSS / JS / API client / renderers 未分層。
5. Composer controls 目前是靜態視覺元件，尚未成為真正的 model / workspace / profile 控制面。
6. Tools / Decision 面板是靜態骨架，尚未完整接 Management Chain、MCP、Patch、Shell approval。
7. 缺少前端契約測試與 API parity 測試，導致 UI 可呼叫不存在的 endpoint。

## 2. 外部參考萃取

`nesquena/hermes-webui` 可吸收的工程理念：

- No-build：Python + Vanilla JS，不引入不必要 bundler。
- Three-panel layout：左側 sessions/navigation，中間 conversation/workbench，右側 workspace browser。
- Composer footer controls：model、profile、workspace 在輸入時仍可見。
- Workspace browser：檔案樹、inline preview、路徑安全檢查。
- Control center：全域設定集中，不讓主要任務區被控制項淹沒。
- 靜態資產拆分：即使 no-build，也應拆成 `static/index.html`、`style.css`、`ui.js`、`workspace.js` 等模組。
- 以測試守住 endpoint、workspace、安全與 UI 行為。

不建議直接照搬：

- Hermes WebUI 的 session / cron / messaging 全量系統，因為本專案目前主線是 Management Decision Layer + MCP Governance。
- 未經治理的 shell / file mutation UI。Hermes 必須維持 Risk Gate、Approval、Auditor。

## 3. 本地 UI 現況

目前 `hermes/api/dashboard.html` 已具備：

- 左側 sidebar：Workbench / Projects / Skills / Settings。
- 中間 main content：session header、message stream、composer。
- 右側 workspace area：Files / Decision / Tools tabs。
- Management Chain 視覺節點：L1 Executive、L2 Strategy、L3 Operator、L4 Auditor。
- File preview overlay。
- Log polling：透過 `/api/logs` 更新 tool call/result/reply。

這是正確方向，但目前比較像「前端先行的 workbench mock」，後端契約尚未同步。

## 4. 主要缺口與風險

### P0-1：Files API 契約不一致

Dashboard 使用：

```text
GET /api/files/list?path=...
GET /api/files/read?path=...
```

FastAPI `hermes/api/server.py`：

```text
有 /api/files/list
缺 /api/files/read
```

輕量啟動器 `start_hermes.py`：

```text
缺 /api/files/list
缺 /api/files/read
```

直接結果：

```text
右側 Files tab 顯示 Failed to load files
```

策略：

- 建立共同 file API helper，避免兩個 server 寫兩套不同邏輯。
- `server.py` 與 `start_hermes.py` 都必須支援同一組 dashboard endpoints。
- `/api/files/read` 必須有大小限制、UTF-8 fallback、binary guard、path traversal 防護。

### P0-2：錯誤訊息不可診斷

目前 UI 只顯示：

```text
Failed to load files
```

工程上不足，因為使用者無法知道是：

- endpoint 不存在
- workspace 權限失敗
- path 不存在
- server 未啟動
- JSON 格式錯

策略：

```text
顯示：Failed to load files: 404 /api/files/list not found
提供：Retry、Open logs、Check API status
```

### P0-3：Dashboard 單檔過大

目前 `dashboard.html` 同時包含：

- HTML layout
- design tokens
- component CSS
- API client
- state management
- renderer
- file tree
- task sending
- log polling

策略：

保持 no-build，但拆分：

```text
hermes/api/dashboard.html
hermes/api/static/style.css
hermes/api/static/api.js
hermes/api/static/state.js
hermes/api/static/workspace.js
hermes/api/static/messages.js
hermes/api/static/management.js
hermes/api/static/boot.js
```

### P1-1：Right panel taxonomy 不完整

目前右側 tabs：

```text
Files | Decision | Tools
```

建議改為：

```text
Files | Decision | Activity | MCP | Patch | Shell | Logs
```

但預設只顯示核心 tabs，其餘進入 overflow 或 Control Center，避免右側太擁擠。

### P1-2：Composer controls 不可操作

目前：

```text
Model: Qwen 14B
Workspace: Root
```

是靜態按鈕。

策略：

- Model selector 讀 `/api/models` 或目前 provider config。
- Workspace selector 讀 `/api/workspaces`。
- Profile selector 讀未來 profile registry。
- Controls 狀態送入 `/api/task` request。

### P1-3：Message stream 缺少 settled activity grouping

目前每個 tool call/result 都可能成為一個獨立 card。

更專業的 transcript 節奏：

```text
User message
Assistant reply
Activity: 4 tools used  [expand]
```

策略：

- tool call/result 預設收斂成 Activity row。
- 有錯誤、approval required、blocked 時才升級為醒目卡片。
- Raw JSON 永遠收在 details / side panel。

## 5. 建議最終布局

Desktop：

```text
┌───────────────┬───────────────────────────────────────┬────────────────────────┐
│ Sidebar       │ Main Workbench                         │ Inspector              │
│               │                                       │                        │
│ Workbench     │ Session Header                         │ Files / Decision / ... │
│ Projects      │                                       │                        │
│ Skills        │ Message Stream                         │ Workspace Browser      │
│ Settings      │ - User request                         │ Management Chain       │
│               │ - Hermes reply                         │ MCP tools              │
│ Sessions      │ - Collapsed Activity                   │ Patch/Shell approvals  │
│               │                                       │ Logs                   │
│               │ Composer + model/workspace/profile     │                        │
└───────────────┴───────────────────────────────────────┴────────────────────────┘
```

Mobile / narrow width：

```text
[Top compact header]
[Message Stream]
[Composer]
[Inspector as bottom drawer]
[Sidebar as slide-over]
```

## 6. API Contract 設計

Dashboard 必要 endpoint：

```text
GET  /api/status
GET  /api/logs
POST /api/task
POST /api/metrics/reset

GET  /api/files/list?path=.
GET  /api/files/read?path=README.md

GET  /api/shell/pending
POST /api/shell/approve/{id}
POST /api/shell/execute

GET  /api/patch/pending
POST /api/patch/approve/{id}
POST /api/patch/apply

GET  /api/governance/status
GET  /api/mcp/status
```

所有回應統一：

```json
{
  "ok": true,
  "data": {},
  "error": null
}
```

或：

```json
{
  "ok": false,
  "data": null,
  "error": {
    "code": "PATH_DENIED",
    "message": "Path is outside workspace boundary.",
    "details": {}
  }
}
```

## 7. 分階段實作策略

### Phase A：API Parity 修復

目標：先讓現有 UI 不再失敗。

- [ ] 新增共享 file API helper。
- [ ] `server.py` 支援 `/api/files/read`。
- [ ] `start_hermes.py` 支援 `/api/files/list`。
- [ ] `start_hermes.py` 支援 `/api/files/read`。
- [ ] Dashboard 顯示可診斷錯誤。
- [ ] 新增 API parity tests。

驗收：

```text
用 start_hermes.py 啟動時，Files tab 可以列出 repo 檔案。
點 README.md 可以 preview。
不存在路徑顯示明確錯誤，不是泛用 Failed to load files。
```

### Phase B：No-build Modular Frontend

目標：維持 no-build，但拆分職責。

- [ ] 抽出 `static/style.css`。
- [ ] 抽出 `static/api.js`。
- [ ] 抽出 `static/workspace.js`。
- [ ] 抽出 `static/messages.js`。
- [ ] 抽出 `static/management.js`。
- [ ] 建立 `boot.js` 做事件綁定。
- [ ] `dashboard.html` 只保留結構與 script/link 引用。

驗收：

```text
dashboard.html 低於 250 行。
JS 模組各自低於 350 行。
python -m unittest discover 通過。
瀏覽器無 console error。
```

### Phase C：Inspector Panel 重整

目標：右側從 tabs demo 變成 Agent OS inspector。

- [ ] Files：workspace browser + preview。
- [ ] Decision：L1-L4 management chain。
- [ ] Activity：tool calls/results grouped by task turn。
- [ ] MCP：server status、registered tools、recent calls。
- [ ] Patch：pending patch approval。
- [ ] Shell：pending shell approval。
- [ ] Logs：raw trace filter。

驗收：

```text
任務執行時，右側能看到 decision、tool、audit 狀態變化。
MCP 任務顯示 MCP_TOOL_CALL / MCP_TOOL_RESULT。
Shell proposal 顯示 pending approval，不會直接執行。
```

### Phase D：Workbench Interaction Polish

目標：像專業工程控制台，不像 demo 頁。

- [ ] Composer controls 變成可操作 selectors。
- [ ] Activity rows 預設 collapsed。
- [ ] Approval required 狀態高亮。
- [ ] Error state 有 retry / logs / copy detail。
- [ ] Sidebar sessions 從 mock 改為 API data。
- [ ] Panel 寬度可 resize 並保存 localStorage。

驗收：

```text
使用者能在單一畫面完成：輸入任務、選模型、看結果、查 trace、批准 patch/shell。
```

## 8. 測試策略

### Python API tests

- `tests/test_dashboard_files_api.py`
- `tests/test_start_server_api_parity.py`
- `tests/test_workspace_security.py`

測試內容：

- path traversal 被拒。
- hidden / forbidden files 被過濾。
- oversized files 被拒或截斷。
- binary file preview 不 crash。
- FastAPI 與 lightweight server endpoint contract 一致。

### Frontend static tests

無 build 也應做最低限度檢查：

```text
node --check hermes/api/static/*.js
```

若沒有 Node，至少新增 Python smoke test：

- dashboard references existing static files
- required DOM ids exist
- required API paths 出現在 API contract list

### Manual browser verification

- 1440px desktop。
- 1280px laptop。
- 768px tablet。
- 390px mobile。

檢查：

- 無重疊。
- message stream 可滾動。
- file panel 可滾動。
- preview overlay 可關閉。
- long markdown / code block 不撐破 layout。

## 9. 設計原則

```text
Reply first.
Decision visible.
Evidence on demand.
Approval prominent.
Failure loud.
No-build, but not no-architecture.
One API contract, two server implementations.
```

## 10. 優先決策

最適合立刻做的不是美化，而是：

```text
P0：修 API contract parity，讓 Files tab 真正可用。
P1：把 dashboard 單檔拆成 static modules。
P2：把右側 tabs 擴充成 Agent OS Inspector。
P3：建立瀏覽器與 API regression tests。
```

這樣 Hermes 才會從「看起來像 Workbench」升級成「工程上可信的 Workbench」。

