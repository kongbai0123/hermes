# Hermes Markdown Preview / Leaf-Inspired Reading Plan

## Goal

Build a Leaf-inspired Markdown reading workflow inside Hermes without making Leaf a hard runtime dependency.

Hermes should first provide safe built-in Markdown preview and report-reading capabilities. Leaf remains an optional external viewer that can only be proposed through governance.

## P0 Dashboard Markdown Preview

Status: implemented.

- Add Markdown preview panel for workspace files.
- Support raw / preview toggle.
- Render TOC sidebar from headings.
- Support in-document search highlighting.
- Render frontmatter, tables, code blocks, headings, lists, and inline code.
- Keep rendering client-side and read-only through Files API.

Validation:

- `tests.test_markdown_preview`
- Dashboard contract checks for `markdown-preview-panel`, `markdown-toc-sidebar`, `markdown-search-input`, and `HermesMarkdownPreview`.

## P1 Agent Report Reading Tools

Status: implemented.

Tools:

- `read_markdown_report(path)`
- `preview_report(path)`
- `extract_markdown_toc(path)`

These tools use `SafeExecutor` path validation and return `ToolResult` with content, summary, and TOC metadata.

Validation:

- Executor reads `tests/fixtures/markdown_report.md`.
- ToolRegistry exposes all report tools as read-only tools.

## P2 Watch-Like Refresh

Status: implemented.

- Add `stat_workspace_file()`.
- Add `/api/files/stat` and `/files/stat` route parity.
- Add `HermesApi.statFile()`.
- Dashboard tracks `lastPreviewSignature` and refreshes the currently previewed file when its signature changes.

Validation:

- File stat returns `mtime`, `size`, and `signature`.
- Dashboard declares `autoRefreshPreview()` and `schedulePreviewRefresh()`.

## P3 Leaf Optional Adapter

Status: implemented.

- Add `propose_leaf_inline_preview(path)`.
- It does not install Leaf.
- It does not execute Leaf.
- It only returns a governed proposal for `leaf --inline <file>`.

Validation:

- ToolResult metadata includes `executes: false`, `permission: read`, and `requires_approval: true`.
- ToolRegistry exposes the adapter as `write_proposal`.

## P4 Governance Integration

Status: implemented.

- ManagementPolicy classifies Leaf preview requests as `leaf_preview`.
- ManagementOrchestrator maps the task to `propose_leaf_inline_preview`.
- External execution remains approval-gated.

Restrictions:

- No automatic Leaf installation.
- No direct shell execution.
- No direct watch process.
- No bypass of Management Layer, Risk Gate, ToolRegistry, or Trace.

## Next Improvement Candidates

- Persist Markdown preview mode per user setting.
- Add code syntax language badges.
- Add section jump keyboard shortcuts.
- Add optional governed `leaf --inline` execution after explicit user approval.
- Add long-running process lifecycle management before any `leaf --watch` support.
