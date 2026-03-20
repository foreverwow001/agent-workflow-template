# Project Maintainers Surface

這個目錄是給 downstream / 新專案本身使用的 supporting maintainer surface。

用途：

- 保存新專案自己的 chat handoff 與跨 session 摘要
- 保存可能值得回 upstream 的 improvement candidates
- 明確區分 template repo 的 `maintainers/` 與 downstream 專案自己的維護面
- 讓第一次 bootstrap 後，新專案不必再手動建立 chat handoff skeleton

治理原則：

- 這裡不是 workflow authoritative rule source
- authoritative project docs 仍以 `project_rules.md`、`doc/implementation_plan_index.md`、`doc/plans/*`、`doc/logs/*` 為主
- upstream 只提供這個 skeleton 與 template；新專案後續產生的 dated handoff / archive / improvement candidate 內容屬於 downstream local overlay

目前建議結構：

- `chat/`：session handoff 與 archive
- `improvement_candidates/`：待驗證、待 promotion 的 reusable candidate 區
