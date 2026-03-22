# Obsidian Vault 建議結構與 Frontmatter 範本

> 建立日期：2026-03-20
> 性質：Active supporting doc
> 用途：提供 Obsidian vault 的建議資料夾結構、命名方式與 note frontmatter 範本，供 reviewed-sync 導入前使用。

## 1. 設計目標

這份建議不是要把 Obsidian 變成 workflow 的正式寫入面，而是要讓它成為：

- 經 review 後的知識整理層
- 可追溯的閱讀與索引層
- repo-first workflow 的輔助記憶層

因此 vault 結構的核心要求只有三個：

1. 區分 pending 與 reviewed
2. 保留來源可追溯性
3. 避免把 vault 誤用成第二個 authoritative source

若 workflow 會在 Dev Container 中直接讓 agent 讀取 Obsidian，推薦把這份結構視為「受控 mount 的來源面」，而不是單純的人類筆記樹。

## 2. 建議資料夾結構

建議從以下最小結構開始：

```text
ObsidianVault/
  00-indexes/
    README.md
    workflows.md
    projects.md
    topics.md
  10-inbox/
    reviewed-sync-candidates/
    pending-review-notes/
  20-reviewed/
    agent-workflow-template/
      workflow-knowledge/
      maintainer-sops/
    <downstream-project-name>/
      project-goals/
      project-planning/
      structure-plan/
      business-reference/
      decision-records/
      development-reference/
    lessons-learned/
  30-archives/
    rejected/
    superseded/
```

這份結構的推薦使用方式是：

- `00-indexes/` 與 `20-reviewed/` 作為主要 read-only mount 區
- `10-inbox/pending-review-notes/` 作為 downstream default 的 writable inbox zone，且只在 capture / triage 命中時 on-demand read
- `10-inbox/reviewed-sync-candidates/` 對 downstream 預設不提供 read 或 write
- `30-archives/` 預設不提供給 agent 讀取

若同時存在 workflow template repo 與 downstream project repo，建議不要共用同一套 mount 權限，而是依 repo 角色切成不同 access profile。

## 3. 每層用途

### 3.1 `00-indexes/`

放入口頁、主題索引、MOC 類整理頁。

這一層只做導覽與知識關聯，不承擔原始來源。

### 3.2 `10-inbox/`

放尚未完成 review 的候選內容。

這裡可以放：

- Web Clipper 收進來的原始文章、影片頁、highlight、transcript capture
- 待整理的同步候選摘要
- 待判斷是否 reusable 的筆記
- 待 review 的整理筆記

這裡不應被當成穩定知識區。

在受控 mount 模式下：

- `pending-review-notes/` 可作為 downstream default 的 writable inbox zone，但不屬於啟動前置閱讀面，只在 capture / triage 命中時 on-demand read
- `reviewed-sync-candidates/` 對 downstream 不應提供 read 或 write

### 3.3 `20-reviewed/agent-workflow-template/`

放 workflow template 自身已確認、可長期查詢的知識。

建議至少包含：

- `workflow-knowledge/`
- `maintainer-sops/`

這一層適合保存例如：如何使用 workflow template 開發新專案、workflow 用法與講解、maintainer 操作規範等內容。

### 3.4 `20-reviewed/<downstream-project-name>/`

放單一開發專案已確認、可長期保留的知識與參考材料。

建議至少包含：

- `project-goals/`
- `project-planning/`
- `structure-plan/`
- `business-reference/`
- `decision-records/`
- `development-reference/`

對應你目前的使用情境，這一層適合保存：

- 專案目標
- 專案規劃
- 結構設計與 structure plan
- 公司基本資料與業務 reference，例如食材、供應商、產品、配方
- 已確認的設計決策
- 其他已整理過、值得 agent 長期查詢的開發參考資料

### 3.5 `20-reviewed/lessons-learned/`

放跨 repo 或跨任務仍有參考價值的共通知識。

這一層適合收斂已經不只屬於單一 repo、但仍值得長期保留的 lessons learned。

### 3.6 `30-archives/`

放被淘汰、被取代、或 review 後決定不保留的材料。

這一層預設不建議 mount 給 agent，避免把低訊號或歷史材料大量帶入工作流上下文。

## 4. 推薦 mount 策略

若要在 Dev Container 中直接使用 Obsidian 內容，推薦採用受控 mount：

- read-only mount
  - `00-indexes/`
  - `20-reviewed/agent-workflow-template/workflow-knowledge/`
  - `20-reviewed/agent-workflow-template/maintainer-sops/`
  - `20-reviewed/<downstream-project-name>/project-goals/`
  - `20-reviewed/<downstream-project-name>/project-planning/`
  - `20-reviewed/<downstream-project-name>/structure-plan/`
  - `20-reviewed/<downstream-project-name>/business-reference/`
  - `20-reviewed/<downstream-project-name>/decision-records/`
  - `20-reviewed/<downstream-project-name>/development-reference/`
  - `20-reviewed/lessons-learned/`
- default writable mount
  - `10-inbox/pending-review-notes/`
- default no-mount
  - `10-inbox/reviewed-sync-candidates/`
  - `30-archives/`
  - 私人草稿或未整理區

目標是讓 agent 能直接讀必要知識，但不因為方便而取得整個 vault 的預設讀寫權限。

### 4.1 Downstream Project Repo Profile

對一般開發專案 repo，建議把 Obsidian access 壓到最小，預設只提供「讀正式知識、寫待審區」這種受限模式。

推薦權限如下：

- allow read
  - `00-indexes/`
  - `20-reviewed/`
- allow write
  - `10-inbox/pending-review-notes/`
- deny read
  - `10-inbox/reviewed-sync-candidates/`
  - `30-archives/`
  - 私人草稿或未整理區
- deny write
  - `00-indexes/`
  - `20-reviewed/`
  - `10-inbox/reviewed-sync-candidates/`
  - `30-archives/`

這種模式適合把 downstream project repo 視為知識消費者：

- 可以讀已 review 的穩定知識
- 可以把新的觀察、疑問、待整理材料丟進 `pending-review-notes/`
- 不直接改寫正式知識區
- 不接觸 candidate staging 區與 archive 區

這裡的下游治理結論已固定：downstream project repo 只允許把新的 observation、疑問、待整理材料丟進 `pending-review-notes/`；`reviewed-sync-candidates/` 仍維持 workflow template repo 的 candidate staging 區，不提供 downstream read / write。

### 4.2 Workflow Template Repo Profile

對 workflow template repo，可以給比較高的權限，因為它本來就承擔流程設計、知識整理、規範調整與 reviewed-sync 治理工作。

你提出的「在 workflow template repo 中可以 read / write 所有資料夾及文檔」技術上可行，但文件治理上建議分成兩層理解：

- filesystem / mount 權限可以較完整
- workflow 規則仍然不應讓 agent 無條件直接改寫所有區域

比較穩的做法是：

- allow read
  - `00-indexes/`
  - `10-inbox/`
  - `20-reviewed/`
  - `30-archives/`
- allow write
  - `10-inbox/pending-review-notes/`
  - `10-inbox/reviewed-sync-candidates/`
  - `00-indexes/`
  - `20-reviewed/`
  - `30-archives/`

若 workflow template maintainer 已明確決定在本機 Dev Container 中採 full curator profile，也可以把整個 vault 直接 mount 進 container，例如統一掛到 `/obsidian/vault`。

目前這個 workflow template repo 的 Dev Container 實作，已直接採用這個 full-vault mount 版本，作為 maintainer-local 預設工作模式。

這種 full-vault mount 只適合 workflow template repo 的 maintainer-local 環境，不應視為 downstream project repo 的預設配置。

但即使在 workflow template repo，也建議保留流程限制：

- 原始 capture 優先寫進 `pending-review-notes/`
- 整理後候選內容優先寫進 `reviewed-sync-candidates/`
- 只有在 user 明確要求或 maintainer review 完成後，才把內容移進 `20-reviewed/`
- `30-archives/` 應視為低頻整理區，不建議當日常工作區使用

也就是說，workflow template repo 可以是 full-access operator，但不應因此放棄 staged promotion 流程。

### 4.3 建議結論

因此，對你列出的兩個問題，正式建議是：

1. 可以。對 downstream project repo，可以設定成只讀 `00-indexes/`、`20-reviewed/`，只寫 `10-inbox/pending-review-notes/`。
2. 也可以。對 workflow template repo，可以給更完整的 read / write 權限。

但更精確的說法應該是：

- downstream project repo 用 restricted consumer profile
- workflow template repo 用 full curator profile

這樣既符合你要的邊界，也比較容易長期維持乾淨的知識治理。

## 5. Capture -> Synthesis -> Reviewed 正式流程

若要把 Obsidian 當成長期記憶層，同時又保留 workflow 的可控性，推薦的主流程如下：

1. 用 Obsidian Web Clipper 做 capture
2. 把原始內容落在 `10-inbox/pending-review-notes/`
3. 用 VS Code + 模板 + agent 對 capture 做理解、整理、摘要、分類與 takeaways 萃取
4. 把整理後輸出寫到 `10-inbox/reviewed-sync-candidates/`
5. 經人工 review 後，再移入 `20-reviewed/` 的對應正式區域

一句話講清楚：

> Obsidian 負責 capture，VS Code 負責理解與加工，`20-reviewed/` 負責沉澱給後續 workflow / project 直接讀取。

這個流程比「在 Obsidian 內把所有事一次做完」更穩，因為它把原始來源、加工中的候選材料、正式知識區分開了。

### 5.1 Capture 階段

Capture 階段的目標只有四件事：

- 把來源收進 vault
- 保留 URL / title / captured_at / highlight / transcript 等原始脈絡
- 盡量少加工
- 不要在這一層直接升格為正式知識

在這個結構下，capture note 建議先進：

- `10-inbox/pending-review-notes/`

原始 clip note 不應直接改寫成正式知識；整理應該產生新的 synthesized candidate，而不是覆蓋 capture 原文。

### 5.2 Synthesis 階段

Synthesis 階段由 VS Code + 你的模板 + agent 執行，重點是：

- 真的理解內容
- 對齊目前 workflow / project 的上下文
- 產生可 review、可沉澱的輸出

這一層適合做：

- 自動摘要
- 分類
- 生成 takeaways
- 判斷和哪個 repo / project 有關
- 判斷應該進哪個正式資料夾
- 補上 frontmatter、tags、status、scope、模板版本

Synthesis 輸出建議先進：

- `10-inbox/reviewed-sync-candidates/`

這一層不是最終知識，而是待 review 的 candidate。

### 5.3 Reviewed 沉澱階段

只有經 review 的內容，才應進 `20-reviewed/`。

推薦落點如下：

- workflow template 的 confirmed 方法、SOP、用法解說
  - `20-reviewed/agent-workflow-template/workflow-knowledge/`
  - `20-reviewed/agent-workflow-template/maintainer-sops/`
- 開發專案的 confirmed 長期參考資料
  - `20-reviewed/<downstream-project-name>/project-goals/`
  - `20-reviewed/<downstream-project-name>/project-planning/`
  - `20-reviewed/<downstream-project-name>/structure-plan/`
  - `20-reviewed/<downstream-project-name>/business-reference/`
  - `20-reviewed/<downstream-project-name>/decision-records/`
  - `20-reviewed/<downstream-project-name>/development-reference/`
- 跨 repo 共用的穩定洞察
  - `20-reviewed/lessons-learned/`

這樣後續 workflow / project 讀到的是已整理、已 review 的知識，而不是原始雜訊流。

### 5.4 Agent 的讀寫規則

這套流程的核心，不是讓 agent 預設可寫整個 vault，而是：

- 預設讀取：`00-indexes/` 與 `20-reviewed/`
- 預設 writable inbox zone：`10-inbox/pending-review-notes/`，用於 capture / triage 命中時的正式支援寫入
- `10-inbox/pending-review-notes/` 不屬於啟動前置閱讀面，只在 capture / triage 命中時 on-demand read
- 預設不讀不寫：`10-inbox/reviewed-sync-candidates/`
- 預設不寫入：`20-reviewed/` 與 `30-archives/`

這樣才同時兼顧：

- 長期記憶可用性
- 流程穩定性
- 人工成本不被放大
- 正式知識區不被自動摘要污染

若你採用 repo-specific profile，這段規則應再細分成：

- downstream project repo
  - 預設讀取：`00-indexes/`、`20-reviewed/`
  - 預設寫入：`10-inbox/pending-review-notes/`
  - 預設不讀不寫：`10-inbox/reviewed-sync-candidates/`、`30-archives/`
- workflow template repo
  - 可讀取全部區域
  - 可在明確流程下寫入各區
  - 但仍應優先遵守 inbox -> candidate -> reviewed 的 promotion 路徑

對 downstream project repo 的 workflow 啟動順序，建議再加一條固定操作規則：

1. 先檢閱 `00-indexes/` 的索引頁
2. 再依索引受控讀取最小必要的 `20-reviewed/` 文件
3. 啟動階段不讀 `10-inbox/reviewed-sync-candidates/`、`30-archives/` 與其他未列入 allow-list 的 vault 路徑
4. `10-inbox/pending-review-notes/` 不作為啟動前置閱讀來源；只有 user 明確要求處理 capture / triage，或 workflow 命中 recorder 路徑時，才進一步 read / write

這樣 downstream workflow 會先用 index 做 routing，再讀正式 reviewed knowledge，而不是直接對 vault 做廣泛掃描。

### 5.5 Pending Review Notes 的 Dedupe / Update 規則

若允許 agent 自動把 triage 類事件寫入 `10-inbox/pending-review-notes/`，一定要先有比一般筆記更嚴格的 dedupe / update 規則，否則很快就會堆出大量相似 note。

建議預設採用以下規則：

1. 同一事件優先 update，不優先新增
2. 只有跨模組、跨根因、跨風險類型時，才新增新 note
3. note 必須有穩定的 dedupe key，不能只靠自然語言標題判斷

推薦的 dedupe key 組成：

- `project_scope`
- `recorded_by_role`
- `event_class`
- `module_area`
- `symptom_signature`

其中 `symptom_signature` 應是去敏、短字串、可穩定比較的摘要，例如：

- `pytest-login-seeded-admin-failure`
- `npm-build-missing-env-schema`
- `authz-admin-endpoint-missing-check`

推薦 update 規則如下：

- 若 dedupe key 相同，且事件仍屬同一問題，更新既有 note
- 若 dedupe key 相同，但 impact 或 evidence 有新增，附加到同一 note
- 若 dedupe key 相同，但根因已確認且事件性質改變，可在原 note 中更新狀態，不另開新 note
- 若 dedupe key 不同，才建立新 note

推薦 merge 條件如下：

- 同模組
- 同症狀
- 同角色視角
- 同一工作階段或短時間內重複發生

推薦 split 條件如下：

- 同一模組但其實是不同 root cause
- 同一錯誤表象，但 security / QA / engineer 的處理上下文明顯不同
- 同一問題已從 observation 變成 confirmed design decision 或正式 defect tracking 項目

為避免 note 爆量，建議 agent 自動記錄時遵守以下 update 策略：

- 先搜尋同 dedupe key 的既有 note
- 若找到，更新 `last_seen_on`、`occurrence_count`、`evidence_refs`
- 若沒找到，再建立新 note
- 同一 session 內若連續命中同事件，不重複建立第二份 note

另外建議保留三條硬限制：

- 不寫整包 raw log / stack trace
- 不寫 secrets、token、個資、敏感 payload
- 不因為自動記錄而直接升格為 reviewed / decision 類知識

### 5.6 Pending Review Notes 標準欄位

若 `pending-review-notes/` 要承接 engineer、QA、security reviewer 的 triage 記錄，建議使用專用欄位，而不是沿用 reviewed note 或 candidate note 的最小格式。

建議最小欄位如下：

- `title`
- `note_kind`
- `source_repo`
- `project_scope`
- `recorded_by_role`
- `detection_mode`
- `event_class`
- `workflow_phase`
- `current_status`
- `impact_level`
- `reproducibility`
- `module_area`
- `symptom_signature`
- `occurred_on`
- `last_seen_on`
- `occurrence_count`
- `evidence_refs`
- `workaround_applied`
- `next_owner`
- `tags`

欄位說明：

- `note_kind`: 固定為 `pending-review-note`
- `recorded_by_role`: `engineer`、`qa`、`security-reviewer`
- `detection_mode`: `auto` 或 `manual`
- `event_class`: `blocker`、`qa-defect`、`security-signal`、`workaround`、`user-requested-record`
- `workflow_phase`: `implementation`、`testing`、`security-review`
- `current_status`: `pending-triage`、`watching`、`blocked`、`needs-owner`
- `impact_level`: `low`、`medium`、`high`、`critical`
- `reproducibility`: `unknown`、`intermittent`、`reproducible`
- `symptom_signature`: 用於 dedupe / update 的穩定摘要鍵
- `evidence_refs`: 放測試名稱、命令、檔案路徑、CI run id、ticket id 等 reference，不直接貼 raw output

### 5.7 Pending Review Note 範本

適用於尚未定案、但值得留在 triage 流程中的工作事件。

```yaml
---
title: auth test keeps failing in seeded env
note_kind: pending-review-note
source_repo: <downstream-project-name>
project_scope: <downstream-project-name>
recorded_by_role: qa
detection_mode: auto
event_class: qa-defect
workflow_phase: testing
current_status: pending-triage
impact_level: medium
reproducibility: reproducible
module_area: auth/login
symptom_signature: pytest-login-seeded-admin-failure
occurred_on: 2026-03-21
last_seen_on: 2026-03-21
occurrence_count: 2
evidence_refs:
  - pytest tests/test_login.py::test_seeded_admin_login
  - ci run #1234
workaround_applied: false
next_owner: engineer
tags:
  - pending-review
  - qa
  - auth
  - triage
---
```

本文建議段落：

```markdown
# Symptom Summary

一句話描述現在觀察到的問題。

# What Happened

- 發生在哪個步驟
- 觀察到什麼現象
- 是否可重現

# Impact

- 卡住誰
- 影響哪個流程
- 目前嚴重度判斷

# Evidence Summary

- 測試名稱 / command / 異常摘要
- 相關檔案或模組
- 不貼整包 raw log

# Workaround

- 是否已有暫時解法
- 如果有，代價是什麼

# Next Action

- 下一步要誰處理
- 需要補什麼資訊
- 是否可能升格為 candidate / reviewed knowledge
```

### 5.8 Agent 自動記錄觸發規則

若要讓 agent 自動把工作事件寫進 `pending-review-notes/`，建議採 allow-list + safety gate 模式，而不是全量自動紀錄。

共通規則：

1. 只有命中允許事件類型時，才可自動寫入
2. 自動寫入前先套用 dedupe / update 規則
3. 只寫摘要與 evidence reference，不寫 raw output dump
4. 一律標記 `current_status: pending-triage`
5. 不得直接升格為 reviewed note、candidate note 或正式 decision

允許自動寫入的事件類型：

- 重複失敗或持續 blocker
- 已可重現但未定級的 QA 問題
- 需要後續 triage 的安全訊號
- 為了繼續工作採用 workaround
- user 明確要求留痕的事件

其他事件預設不自動記錄；若需要保留，應由 user 明確要求。

### 5.9 Engineer / QA / Security Reviewer 角色規則

#### Engineer

適合自動寫入：

- 同一類失敗重複出現，且已阻斷實作
- 為了繼續工作必須採用 workaround
- 同模組反覆出現環境或依賴問題，短時間內無法排除
- user 明確要求把某個實作問題留下 triage 記錄

不應自動寫入：

- 開發中預期會出現的紅燈
- 剛改到一半的編譯或測試失敗
- 一次性 typo、立即修掉的 lint / type issue

#### QA

適合自動寫入：

- 缺陷已可重現，但 root cause 與 owner 尚未定
- flaky failure 在同一輪驗證中重複出現
- 驗收標準不完整，已影響 pass / fail 判定
- user 明確要求保留這次驗證問題

不應自動寫入：

- 單次且無法重現的失敗
- 操作失誤造成的無效結果
- 沒有任何 evidence 的主觀懷疑

#### Security Reviewer

適合自動寫入：

- 出現可信的安全訊號，需要後續 triage
- 發現缺少關鍵 hardening evidence
- 掃描工具或人工 review 指出有風險面，但仍待確認 exploitability 或影響範圍
- user 明確要求留痕的安全觀察

不應自動寫入：

- 含 exploit 細節、敏感 payload、token、secret 的原始輸出
- 尚未整理的完整掃描報表
- 已接近正式漏洞結論、需要進一步人工定級的內容
- 不具可信 evidence 的高嚴重度判斷

### 5.10 模板分層

建議把模板分成兩層，而不是只用一份模板：

- Capture template
  - 給 Web Clipper 或原始來源入庫用
  - 偏原文與 metadata 保存
- Synthesis template
  - 給 VS Code / agent 做整理後輸出用
  - 偏摘要、分類、takeaways、採用判斷與正式落點建議

這樣做的好處是：

- 原始來源可追溯
- 整理邏輯可持續優化
- 正式知識不會和原始素材混在一起

## 6. 命名建議

建議採用以下命名原則：

- index 類：`topics.md`、`projects.md`、`workflow-knowledge.md`
- reviewed note 類：`2026-03-20-reviewed-sync-policy-summary.md`
- decision 類：`2026-03-20-obsidian-role-decision.md`
- candidate 類：`2026-03-20-agent-workflow-template-handoff-summary.md`

若一份 note 主要來自 repo 文件，檔名應保留日期與主題，不必強求和原檔同名，但應能從 frontmatter 回追來源。

## 7. Frontmatter 最小欄位

所有同步到 Obsidian 的 note，建議至少包含以下欄位：

- `title`
- `source_repo`
- `source_path`
- `source_type`
- `review_status`
- `promotion_status`
- `synced_on`
- `tags`

可選欄位：

- `source_date`
- `reviewed_by`
- `supersedes`
- `related_topics`
- `related_projects`

## 8. Reviewed Note 範本

適用於已通過 review、可長期保留的知識筆記。

```yaml
---
title: reviewed sync policy summary
source_repo: agent-workflow-template
source_path: maintainers/chat/2026-03-20-project-maintainers-obsidian-sync-policy.md
source_type: maintainer-policy
review_status: approved
promotion_status: reviewed
synced_on: 2026-03-20
source_date: 2026-03-20
reviewed_by: human
tags:
  - workflow
  - obsidian
  - reviewed-sync
  - knowledge-layer
related_topics:
  - repo-first
  - memory-governance
related_projects:
  - agent-workflow-template
---
```

本文建議段落：

```markdown
# Summary

一句話說明這份 note 留下來的原因。

# Key Points

- point 1
- point 2
- point 3

# Source Notes

- 這份內容是經 review 後整理，不是新的 authoritative source。
- 真正來源仍在 repo 的 `source_path`。
```

## 9. Inbox Candidate 範本

適用於尚待 review 的候選同步內容。

這個範本對應的是 `10-inbox/reviewed-sync-candidates/`，不是 `10-inbox/pending-review-notes/`。

```yaml
---
title: candidate handoff summary
source_repo: agent-workflow-template
source_path: project_maintainers/chat/handoff/example.md
source_type: handoff-summary
review_status: pending
promotion_status: local-only
synced_on: 2026-03-20
tags:
  - inbox
  - candidate
  - handoff
related_projects:
  - agent-workflow-template
---
```

本文建議段落：

```markdown
# Why This Is In Inbox

說明為什麼這份內容值得暫存，但還不能進 reviewed。

# Reusability Check

- 哪些部分可能可跨專案重用
- 哪些部分仍然太專案化

# Next Review Action

- 需要補什麼 evidence
- 需要誰決定是否晉升
```

## 10. Index Note 範本

適用於 vault 內的入口頁或主題索引頁。

```yaml
---
title: workflow knowledge index
source_repo: none
source_path: none
source_type: index
review_status: approved
promotion_status: reviewed
synced_on: 2026-03-20
tags:
  - index
  - workflow
  - knowledge-map
---
```

本文建議段落：

```markdown
# Workflow Knowledge Index

## Policies

- [[reviewed sync policy summary]]

## SOPs

- [[portable workflow checklist]]

## Lessons Learned

- [[bootstrap hardening lessons]]
```

## 11. 第一次建立 vault 時的最小實作

如果你現在要開始設定，最小可行版本只要先做這些：

1. 建立 `00-indexes/`、`10-inbox/`、`20-reviewed/`、`30-archives/`
2. 先建立一份 index note
3. 先挑一份已 review 的 repo 文件，建立第一份 reviewed note
4. 定義 read-only mount、`pending-review-notes` 的 default writable + on-demand read 邊界，以及 `reviewed-sync-candidates` 的 downstream no-read/no-write 邊界
5. 先建立至少一份 capture template 與一份 synthesis template
6. 先不要做整包可寫 mount、雙向同步或腳本化 ingest

## 12. 不要做的事

- 不要把整個 repo 直接當 vault 根目錄
- 不要把 reviewed 與 pending 混在同一層
- 不要省略 `source_repo` 與 `source_path`
- 不要在 Obsidian 內產生和 repo 競爭的 authoritative 規則版本
- 除非是 workflow template repo 的 maintainer-local 明確 opt-in 配置，否則不要把整個 vault 以可寫方式掛進 Dev Container
- 不要讓 agent 預設寫入 `20-reviewed/` 或 `30-archives/`
- 不要把 Web Clipper 的原始 capture 直接升格成正式知識
- 不要讓 AI 直接覆蓋原始 capture note

## 13. 與相關文件的關係

- 政策邊界：`2026-03-20-project-maintainers-obsidian-sync-policy.md`
- 前置 checklist：`2026-03-20-obsidian-reviewed-sync-checklist.md`

這份文件提供結構與格式範本，不取代 reviewed-sync 政策本身。
