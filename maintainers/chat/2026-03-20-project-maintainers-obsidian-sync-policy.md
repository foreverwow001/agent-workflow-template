# Obsidian 記憶整合與 Project Maintainers 同步政策

> 建立日期：2026-03-20
> 性質：Active maintainer policy
> 用途：整合 Obsidian 記憶方式分析與 downstream `project_maintainers/` 同步政策，作為目前單一 maintainer 參考文件。

## 1. 結論

這個 workflow template 適合吸收 Obsidian / persistent memory 的方法論，但不適合把 Obsidian 升格為正式 workflow 的唯一真相來源。

對 downstream `project_maintainers/` 的推薦政策是：

- repo-first
- reviewed sync
- repo -> Obsidian 單向晉升

更直接地說：

1. `project_maintainers/` 先保留在 downstream repo 內，作為 project-local supporting memory
2. Obsidian 只承接經人工 review 的高訊號內容
3. Obsidian 不應成為 active workflow、authoritative rules 或 `project_maintainers/` 的唯一寫入面
4. 若 agent 需要在 Dev Container workflow 中直接讀取 Obsidian 內容，建議使用受控 mount，而不是整包掛載或臨時複製

## 2. 背景與判斷基礎

本次整理吸收的外部思路，核心不是單純把筆記放進 Obsidian，而是建立共享知識與檢索層：

- Obsidian vault 作為人工整理與策展入口
- 全文或語意檢索作為 AI 可查詢的知識層
- 多 session / 多 agent 可重用同一份高訊號知識
- 透過 Hot / Warm / Cold 分層降低 context drift
- 透過 promotion pipeline 讓短期經驗逐步升格為穩定知識

本 template 與這種方法論相容，但不適合直接照搬外部整套基礎設施，原因在於它本身已經有清楚的 authoritative / supporting / archive 治理邊界。

## 3. 為什麼方法論相容

這個 template 已具備導入分層記憶與檢索思維的前置條件：

1. 已有固定 artifact chain
	- 正式輸出集中在 `doc/implementation_plan_index.md`、`doc/plans/`、`doc/logs/`
	- 高訊號資料已有穩定落點，適合後續索引與晉升

2. 已有跨 session handoff 機制
	- `Chat: Export Chat...` 加 handoff 摘要，本質上就是人工策展的記憶晉升流程

3. 已有 session persistence 概念
	- `.agent/active_sessions.json`、`.agent/.terminal_session.json` 等保存的是執行狀態，可視為熱記憶的一部分

4. 已有治理與收斂原則
	- active truth、historical artifact、supporting docs 的邊界明確，這使記憶系統不容易演變成多重真相來源

## 4. 為什麼不適合直接 Obsidian-first

### 4.1 現有治理模型是 authoritative-source-first

若直接引入 vault-first source of truth，會與既有規則、artifact、handoff、archive 的邊界衝突。

### 4.2 外部方案通常預設 ingest 大量 raw material

例如 terminal session、web clipping、debug capture、原始筆記；但本 template 反而刻意把 runtime state、raw chat JSON、service capture 與敏感 runtime artifact 排除在正式 surface 之外。

### 4.3 AI 自動寫回規則文件風險過高

這裡現有哲學是人工 gate、authoritative docs、規則來源可追溯；若 AI 直接改寫 instruction 或規則文件，會破壞收斂性與可審計性。

## 5. Obsidian 在這個 template 中的正確定位

Obsidian 適合扮演：

- 人工策展層
- Warm / Cold memory 的閱讀與整理介面
- 跨任務、跨 session、跨專案的知識連結層

Obsidian 不適合扮演：

- 正式 plan / log / gate 的唯一寫入層
- workflow authoritative rule source
- runtime session state 的主儲存位置

## 6. 建議的 memory 分層

### 6.1 Hot Memory

- `doc/plans/*.md`
- `doc/logs/*.md`
- active handoff
- active session state

### 6.2 Warm Memory

- 已驗證 SOP
- 穩定 maintainer docs
- release artifacts
- 已整理過的 lessons learned

### 6.3 Cold Memory

- raw chat export JSON
- PTY debug artifact
- execution log
- 歷史 archive 與未晉升的原始捕捉資料

## 7. Project Maintainers -> Obsidian 同步政策

`project_maintainers/` 不應自動同步到 Obsidian。

原因如下：

1. `project_maintainers/` 本質上是 project-local supporting memory 與候選區，不是最終知識庫
2. auto-sync 會放大 repo 與 vault 的雙真相風險
3. 並非所有 project-local 經驗都值得跨 repo 沉澱

其中內容可能包含：

- handoff
- 短期 operational notes
- improvement candidates
- 單一專案才成立的 workaround

若直接整包同步到 Obsidian，vault 很容易退化成第二個未治理的原始收納區。

## 8. 推薦策略：reviewed sync

### 8.1 原則

- repo 內 `project_maintainers/`：canonical project-local supporting memory
- Obsidian：跨 repo 的閱讀、整理、檢索與知識聚合層
- 同步方向：以 repo -> Obsidian 單向同步為主
- 同步 gate：必須先經人工 review
- Dev Container 讀取路徑：優先使用受控 mount，把已核准區域提供給 agent 讀取
- Dev Container 寫入路徑：只在 user 明確要求時，才開放指定 writable zone

### 8.2 最小流程

1. 在 downstream repo 的 `project_maintainers/` 中先記錄 handoff、candidate、decision notes
2. 人工 review，判斷哪些內容屬於高訊號且值得跨 repo 保存
3. 通過 review 的內容再同步到 Obsidian
4. 若最終確認為 reusable knowledge，再 promotion 回 workflow template repo 的正式 doc / skill / SOP

## 9. 建議同步與不同步範圍

### 9.1 預設不同步

- `project_maintainers/chat/handoff/` 內尚未完成 review 的 handoff
- `project_maintainers/improvement_candidates/` 內尚未完成 review 的 candidate
- project-local workaround
- 含 runtime state、原始 transcript、raw export 或敏感資訊的內容
- `doc/plans/*.md`
- `doc/logs/*.md`
- `.agent/workflow_baseline_rules.md`
- `project_rules.md`

### 9.2 可經 review 後同步

- 已完成任務的高品質 handoff 摘要
- 經整理後的 decision record
- 已確認對多個專案都有參考價值的 lessons learned
- 已完成初步 reusable assessment 的 improvement candidate 摘要
- 與 workflow / runtime / skills 相關，且不含 project-private 細節的穩定做法
- 穩定的 maintainer SOP / checklist / analysis
- `maintainers/release_artifacts/*.md` 類型的已整理交付材料

### 9.3 Dev Container 中的推薦存取方式

若 agent 在 Dev Container 中需要直接使用 Obsidian 內容，推薦方式如下：

- 以 read-only mount 提供 `00-indexes/` 與 `20-reviewed/` 等已核准區域
- 視需要提供單一、受控的 writable zone，例如 `10-inbox/reviewed-sync-candidates/`
- downstream project repo 不要把整個 vault 以可寫方式掛進 container
- 不要把未審核區、archive、私人原始材料預設暴露給 agent

補充：workflow template repo 若由 maintainer 在本機 Dev Container 明確選擇 full curator profile，可例外採用 full-vault writable mount；但這仍屬 maintainer-local 操作，不應外推成 downstream repo 預設政策。

目前這個 workflow template repo 的本機 Dev Container 實作，已直接掛入 full-vault mount，作為 maintainer-local 預設工作模式；但這個預設不改變 downstream project repo 仍應維持 restricted consumer profile 的政策。

## 10. 推薦落地順序

1. 先維持 repo 內 markdown artifact 與 `project_maintainers/` 作為正式來源
2. 再定義 Hot / Warm / Cold memory 邊界
3. 先完成 reviewed-sync checklist 與首次手動演練
4. 再補全文索引、MCP search 或其他檢索能力
5. 最後才考慮 candidate promotion automation

操作層前置作業可參考 `2026-03-20-obsidian-reviewed-sync-checklist.md`。

## 11. 一句話規則

不要把 workflow template 變成 Obsidian-first；應該讓 repo-first 的 workflow 多一個經 review 的 Obsidian-backed knowledge layer。
