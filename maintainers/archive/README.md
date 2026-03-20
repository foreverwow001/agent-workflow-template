# Maintainer Archive 規則

> 用途：定義 `maintainers/archive/` 的收錄範圍。這裡只放 **非 chat 專屬** 的 maintainer 歷史文件。

## 1. 與 `chat/archive/` 的差別

- `maintainers/chat/archive/`
  - 只收 maintainer chat 文檔、handoff、draft lineage、chat-oriented 歷史分析
  - 其治理規則以 `maintainers/chat/archive/README.md` 為準

- `maintainers/archive/`
  - 收 **不屬於 chat/handoff** 的 maintainer 歷史文件
  - 例如：已完成的 migration checklist、結案的 maintainer 級專案收尾清單、已不再作為 active truth 的非 chat 規劃文檔

## 2. 什麼該放這裡

符合下列任一條件即可：

1. 文件不是 chat/handoff 類型
2. 文件曾是 maintainer 級工作清單或遷移 checklist
3. 文件已完成，不再作為 active 規格來源
4. 保留它是為了審計、回顧或追溯決策，而不是為了驅動當前實作

## 3. 什麼不該放這裡

以下內容不要放進這裡：

1. 仍是現行規格來源的 active 文檔
2. maintainer chat/handoff 文件
3. 原始 chat export JSON
4. 只是暫時完成、但仍在 repo 中充當 authoritative baseline 的規格文檔

## 4. 當前案例

目前這個目錄的代表案例包括：

- `2026-03-16-copilot-cli-migration-checklist.md`
- `2026-03-18-workflow-optimization-plan.md`

它們適合放在這裡，而不是 `chat/archive/`，因為都屬於 maintainer 級非 chat 歷史文件：前者是 migration checklist，後者是 MT-003 的結案計畫與 closure record。
