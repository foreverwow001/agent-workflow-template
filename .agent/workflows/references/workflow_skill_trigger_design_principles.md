# Workflow Skill Trigger Design Principles

這份文件說明哪些角色需要 checklist 型 trigger，哪些角色不需要，以及判定原則。

## 核心原則

- 只有「同一角色在執行前需要根據條件切換不同 skill 組合」時，才值得建立 checklist
- 若某角色的 skill 載入條件幾乎固定、單一路徑、或完全受 gate 布林值控制，優先用直接規則，不要為了形式一致硬做 checklist
- checklist 的價值在於降低分支判斷歧義，不在於讓每個角色看起來格式一致

## 目前適用角色

### Coordinator

需要 checklist。

原因：
- Research Gate 下存在多種不同觸發來源
- `deep-research` 與 `fact-checker` 可同時或分別命中
- 需要可機械化判定，避免 Coordinator 主觀選擇

### Engineer

需要 checklist。

原因：
- 實作前可能同時命中 refactor、TypeScript / JavaScript、Python 多條件
- 不同 skill 對應不同語言與工作型態
- 若不用 checklist，條件容易在多份文件中漂移

## 目前不適用角色

### Planner

目前不需要 checklist。

原因：
- `project-planner` 幾乎是固定能力入口
- 條件主要是任務是否需要 phase / dependency / estimate / risk 拆解
- 目前沒有多個 planner skill 需要在同一角色內分流

### Security Reviewer

目前不需要 checklist。

原因：
- 一旦 `security_review_required=true` 或命中 security trigger，就固定載入 `security-review-helper`
- skill 載入是 gate-bound，不是多分支 routing

### QA

目前不需要 checklist。

原因：
- QA 的重點是執行 `code-reviewer` 與條件式 `test-runner`
- 這更像 command requirement，不是 skill selection matrix
- 若未來 QA 出現多個互斥或可疊加的審查 skill，再考慮 checklist 化

## 何時要升級成 checklist

若未來出現以下情況，就值得把目前非-checklist 角色升級：

- 同一角色需要在 2 個以上 skill 之間做條件式分流
- 條件可同時命中，且必須明確規定疊加策略
- 不同文件開始重複描述同一組載入條件，已有漂移風險

## 與總索引的關係

- checklist 本身才是 role-specific authoritative source
- 總索引若存在，只能作為導航入口，不能取代各角色 checklist 或直接成為判定依據
