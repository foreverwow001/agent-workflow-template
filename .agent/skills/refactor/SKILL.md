---
name: refactor
description: "Behavior-preserving refactor guidance for Engineer. Use when the task is cleanup, restructuring, extracting functions, reducing code smells, renaming, modularizing, or improving type safety in existing code without adding new behavior."
---

# Refactor

在不改變外部行為的前提下，改善既有程式碼的可讀性、可維護性與結構安全性。

## 何時使用

當任務符合任一條件時，Engineer 應載入本 skill：

- User 或 Planner 明確要求 refactor / cleanup / 重整結構
- 主要工作是拆大函式、拆模組、重新命名、消除重複
- 既有結構讓後續功能難以安全實作
- 你需要降低複雜度、改善型別安全或移除 code smell

## 核心要求

- Refactor 的首要原則是 **preserve behavior**，不是順手加功能
- 優先做小步修改，每一步都保留可驗證狀態
- 若缺乏驗證手段，先補最小安全網，再動結構
- 不要把大規模 refactor 與新功能混成一團；若 unavoidable，要在 Spec 與變更說明中明確切開
- 優先遵守 repo 既有命名、模組邊界與 `project_rules.md`

## Engineer 工作流

1. 先確認這次 refactor 的目標、非目標與不可改變的行為。
2. 先讀 [references/refactor-workflow.md](./references/refactor-workflow.md) 確認安全節奏與停止條件。
3. 再依主要語言載入對應 reference：
	- TypeScript / JavaScript： [references/refactor-typescript-javascript.md](./references/refactor-typescript-javascript.md)
	- Python： [references/refactor-python.md](./references/refactor-python.md)
	- 共通 smell 對照： [references/refactor-smells.md](./references/refactor-smells.md)
4. 先建立或確認最小驗證手段：現有測試、窄範圍 smoke、型別檢查、靜態檢查。
5. 一次只做一類變更：抽函式、改命名、拆模組、消除巢狀、補型別，避免一次混太多。
6. 每一輪 refactor 後都重新驗證，再進下一步。
7. 若發現 refactor 已開始改動外部行為、資料格式或 API 契約，立刻停下並回報 Coordinator。

## 常見輸出期望

- 更小、更聚焦的函式與模組
- 更清楚的命名
- 更少的重複邏輯
- 更淺的控制流程與更明確的 guard clauses
- 更穩定的型別 / 介面邊界

## 參考資料

- [references/refactor-workflow.md](./references/refactor-workflow.md)
- [references/refactor-smells.md](./references/refactor-smells.md)
- [references/refactor-typescript-javascript.md](./references/refactor-typescript-javascript.md)
- [references/refactor-python.md](./references/refactor-python.md)
