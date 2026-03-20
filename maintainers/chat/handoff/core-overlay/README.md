# Core Overlay Handoff Index

> 用途：作為 `handoff/core-overlay/` 這組 maintainer 文件的最短導覽。

## Files

- `daily-sync-sop.md`
  - 日常 upstream 發版與 downstream friction triage 的操作 SOP
- `sync-checklist.md`
  - 將 SOP 進一步收斂成 phase-1 `workflow-core` sync command / release checklist 與 hard-gate 契約
- `cli-spec.md`
  - `workflow-core` 六個 wrapper commands 的 CLI 介面規格，固定參數、exit code 與 stdout/stderr 契約
- `curated-core-v1-landing-checklist.md`
  - 目前 `curated-core-v1` 相對於來源 ref 的 ready / worktree-only / missing 狀態快照
- `curated-core-v1-release-candidate-batch.md`
  - 將 `curated-core-v1` 從 `warn` 推進到 `pass` 的最小 release-candidate 批次定義

> 單次 session handoff 應放在 `maintainers/chat/handoff/` 根目錄；此資料夾只保留長期維護的 core-overlay SOP / checklist / spec。

## Read Order

1. `daily-sync-sop.md`
2. `sync-checklist.md`
3. `curated-core-v1-landing-checklist.md`
4. `curated-core-v1-release-candidate-batch.md`
5. `cli-spec.md`
