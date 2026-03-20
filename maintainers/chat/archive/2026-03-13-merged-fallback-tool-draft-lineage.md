# Merged Fallback Tool Draft Lineage

> 建立日期：2026-03-14
> 狀態：Archived
> 用途：收斂 2026-03-13 三份 fallback draft 文件的歷史脈絡，避免 archive 內保留多份已被正式規格完整吸收的草稿。

---

## 已收斂的草稿

以下三份文件已於 2026-03-14 自 archive 內移除，因為其決策內容已被 active 規格完整吸收：

1. `2026-03-13-merged-fallback-tool-requirements.md`
2. `2026-03-13-merged-fallback-tool-design-v1.md`
3. `2026-03-13-fallback-v1-implementation-checklist.md`

## 為何可移除

三份草稿描述的是同一條演進鏈：

- requirements：定義 v1 要保留與退休的能力
- design：把 requirements 收斂成 package / command / module 邊界
- checklist：把設計稿拆成實作與驗收清單

這些內容後來都已併入 active 文件：

- `maintainers/chat/2026-03-13-merged-fallback-tool-spec.md`

換句話說，active spec 已經同時承擔：

- v1 scope baseline
- namespace / package identity
- bridge / artifact compatibility boundary
- consent / startup contract
- implementation acceptance baseline

因此再保留三份平行草稿，只會增加維護成本與閱讀歧義。

## 保留的歷史價值

若之後需要理解這條演進鏈，應以這個順序閱讀：

1. `2026-03-13-terminal-pty-target-architecture-and-migration-principles.md`
2. `2026-03-13-pty-monitor-and-capture-contract.md`
3. `2026-03-13-merged-fallback-tool-spec.md`

若還需要知道「為什麼草稿被刪」，看本檔即可，不需要回復原始 draft 檔案。
