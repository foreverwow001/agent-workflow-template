# Subtree Sync 前 Mutable Path 拆分清單

> 建立日期：2026-03-19
> 狀態：Active Supporting Doc
> 用途：把目前 repo 中會污染 subtree 的 mutable hotspot 收斂成一份可執行的拆分清單，作為 core sync 落地前的前置工作。

> 先講兩個不可忽略的 framing：
> 1. 目前 repo 最大的 mutable hotspot 是 `.agent/skills`，不是 `.agent/workflows`。
> 2. 目前 repo 最大的路徑耦合點是 `AGENT_ENTRY.md` 對 root 下 `./.agent/...` 與 `./doc/...` live path 的直接假設，所以 subtree 只是運輸機制；真正落地時仍要保留 live path，或提供 projection/bootstrap script，把 curated core 投影回這些 live path。

---

## 1. 這份清單的判定標準

下列任一路徑若符合以下任一條件，就不能直接留在 subtree-managed core 裡：

- 會被 runtime 正常寫入
- 會因 downstream 本地安裝或設定而改動
- 屬於 project-local policy，而不是 portable core truth
- 屬於 generated state、cache 或 audit trail

換句話說，這份清單不是「看起來髒」才拆，而是「正常使用就一定會髒」就必拆。

---

## 2. 拆分優先順序

建議順序如下：

1. 先鎖定 live path continuity，不要讓 subtree 破壞 `AGENT_ENTRY.md` 的入口假設
2. 再拆會讓 subtree 每次使用都 dirty 的 `.agent/skills` runtime-written files
3. 再拆 `.agent/skills` 底下的 project-local policy files
4. 再拆 `.agent/skills` 的 local install destination
5. 最後處理 generated index / cache 類路徑

原因是：

- 第 1 類不先處理，後續即使 export 成功，workflow 入口也會直接失效
- 第 2 到 4 類不拆，subtree 幾乎無法實際運作
- 第 5 類不拆，主要會造成長期噪音與 review 成本

---

## 3. 可執行拆分清單

### Item 0. live path continuity 先定型

- Current coupling:
  - `AGENT_ENTRY.md` 直接要求讀 `./.agent/workflows/dev-team.md`、規則檔與 `./doc/implementation_plan_index.md`
  - workflow / role docs 直接引用 `.agent/skills/**` canonical path
- 問題：如果只是把 curated core 放進 `.workflow-core/`，但沒有把內容重新 materialize / project 回 root live path，整個 workflow 入口會先壞，不需要等到 subtree sync 才發現。
- 注意：`doc/implementation_plan_index.md` 雖然是 required live path，但 ownership 仍屬 downstream overlay artifact；這代表 projection/bootstrap 要保證它存在並可被入口讀到，不代表要把 active index 收回 subtree-managed core。
- 必做動作：在任何 subtree transport 之前，先決定 live path strategy。
- 可接受方案：
  - 保留 root live path，讓 curated core 最終仍落在 `./.agent/**` 與 `./doc/**`
  - 或提供明確 projection/bootstrap script，把 export source 投影回這些 root live path
- 建議交付模型：projection/bootstrap 應作為 core-managed artifact 隨 core 一起交付，例如 `.agent/runtime/scripts/workflow_core_projection.py`，並由 `workflow-core sync apply` 負責呼叫；不要把它做成 downstream 需先自行安裝的獨立 wrapper
- 建議輸出：`./core_ownership_manifest.yml` + `projection/bootstrap` 腳本規格或實作 stub
- 完成判定：fresh downstream workspace 不需要手動改 `AGENT_ENTRY.md`，就能沿用既有入口與 canonical path

### Item 1. skill manifest 改為 overlay state

- Current path: `.agent/skills/_shared/skill_manifest.json`
- 問題：這是 canonical runtime-written registry；只要下載、回滾、同步技能，就會改檔。
- 必做動作：把 canonical write path 從 core tree 移到 overlay state。
- 建議新路徑：`.agent/state/skills/skill_manifest.json`
- 需要連動的程式碼：`._shared` path resolver、manifest reader/writer、external skill download/rollback flow
- 完成判定：正常 skill install/remove 後，core tree 不再出現 manifest diff
- 2026-03-19 implementation status：已落 code。`_shared` helper 現在以 `.agent/state/skills/skill_manifest.json` 為 canonical write path；舊 `_shared/skill_manifest.json` 只保留 read fallback/migration 相容角色。

### Item 2. skill whitelist 改為 project-local config

- Current path: `.agent/skills/_shared/skill_whitelist.json`
- 問題：這不是 portable runtime truth，而是 downstream approval policy。不同專案不應被上游 subtree 覆寫。
- 必做動作：把 whitelist 從 core tree 拆到 overlay config。
- 建議新路徑：`.agent/config/skills/skill_whitelist.json`
- 需要連動的程式碼：whitelist loader、default bootstrap fallback、skill approval checks
- 完成判定：下游可獨立調整 whitelist 而不產生 subtree conflict
- 2026-03-19 implementation status：已落 code。canonical whitelist path 已切到 `.agent/config/skills/skill_whitelist.json`，bootstrap 也改以這個位置建立預設檔；舊 `_shared/skill_whitelist.json` 只保留 read fallback/migration 相容角色。

### Item 3. audit log 改為 generated state

- Current path: `.agent/skills/_shared/audit.log`
- 問題：每次操作都 append，這種檔案放在 subtree-managed core 內一定會污染工作樹。
- 必做動作：把 audit output 改寫到 overlay state。
- 建議新路徑：`.agent/state/skills/audit.log`
- 需要連動的程式碼：audit writer、diagnostics/readme 如有硬編碼路徑需同步
- 完成判定：技能安裝、回滾、同步流程不再修改 core 內任何 log 檔
- 2026-03-19 implementation status：已落 code。audit writer 現在 append 到 `.agent/state/skills/audit.log`；舊 `_shared/audit.log` 不再是 canonical runtime output。

### Item 4. skills index 拆成 core catalog + local overlay index

- Current path: `.agent/skills/INDEX.md`
- 問題：這個檔案現在同時承擔兩種責任：
  - core 內建技能目錄
  - local/external skill 安裝後的更新輸出
- 必做動作：拆成穩定 core catalog 與 local/generated append surface。
- 建議新結構：
  - core: `.agent/skills/INDEX.md`
  - overlay: `.agent/state/skills/INDEX.local.md`
- 需要連動的程式碼：skill converter、github explorer、任何會更新 `INDEX.md` 的 helper
- 完成判定：downstream 安裝外部 skill 時，只改 overlay index，不重寫 core index
- 2026-03-19 implementation status：已落 code。`skill_converter` 現在改寫 `.agent/state/skills/INDEX.local.md`，`.agent/skills/INDEX.md` 改為 builtin-only core catalog，不再承擔 external/local append surface。

### Item 5. external skill install destination 移出 core tree

- Current path pattern: `.agent/skills/<downloaded-skill>/**`
- 問題：目前 external/local skill 直接寫入 `.agent/skills/`，會與 subtree-managed builtin skills 共用同一棵樹。
- 必做動作：將 local/external skill 安裝目的地搬到 overlay 專用目錄。
- 建議新路徑：`.agent/skills_local/**`
- 需要連動的程式碼：external skill path resolver、package layout resolver、rollback cleanup、index generation
- 完成判定：builtin core skills 與 downstream local skills 不再共存同一路徑前綴
- 2026-03-19 implementation status：已落 code。external/local skill 現在安裝到 `.agent/skills_local/**`，manifest 記錄與 rollback cleanup 也已切到新路徑。

### Item 6. `__pycache__` 與 generated cache 全面排除出 managed core

- Current path pattern: `.agent/**/__pycache__/**`
- 問題：雖然可由 ignore 規則遮掉，但若 export source 未嚴格排除，仍會污染 core snapshot。
- 必做動作：在 export/source ownership 規則中明確標記 generated cache 為 excluded。
- 建議做法：
  - export 時硬排除
  - repo ignore 保持完整
- 完成判定：core export 清單不再包含任何 cache/generated bytecode 內容

---

## 4. 建議拆分階段

### Phase 0. Live path contract

這一階段先處理 subtree 落地前的入口可用性：

- 保留 root live path，或
- 寫出 projection/bootstrap script

若這一步沒完成，不要開始 subtree transport。

### Phase 1. Canonical path decouple

這一階段只處理 canonical write path，不動 subtree 本身：

- `skill_manifest.json`
- `skill_whitelist.json`
- `audit.log`

完成後，runtime 最常見的 dirty source 會先消失。

### Phase 2. Local install destination decouple

這一階段處理目錄層級衝突：

- external/local skills 從 `.agent/skills/**` 移到 `.agent/skills_local/**`

完成後，builtin core 與 local additions 才真正分家。

### Phase 3. Catalog split

這一階段處理文件輸出層：

- `INDEX.md` 改成 builtin-only
- local additions 寫到 overlay index

完成後，下載外部 skill 不再觸發 core doc rewrite。

### Phase 4. Export guardrail

這一階段才適合加上 export/subtree guardrail：

- cache exclude
- managed/excluded path enforcement
- export source 驗證

---

## 5. 每一項拆分後必須驗證的事

每完成一項，至少驗證下面四件事：

1. 既有功能仍可運作
2. 新路徑真的被寫入
3. 舊 core 路徑不再被寫入
4. 相關 README / operator 文檔沒有殘留錯誤 canonical path

建議對技能系統至少補以下回歸檢查：

- 安裝 external skill
- rollback external skill
- 更新 manifest
- 生成或更新 index

### Shared verification strategy

由於 `tests/**` 不應進 subtree-managed core，共用驗證不能只靠 repo-level tests directory。

實作前應先固定：

- portable smoke suite 隨 core 一起交付，建議路徑：`.agent/runtime/scripts/portable_smoke/workflow_core_smoke.py`
- `workflow-core release precheck` 在 ownership 檢查後要能呼叫它
- `workflow-core sync verify` 在 subtree apply 與 projection/bootstrap 後要能呼叫它
- 任一 `split_required` 項目宣告完成前，至少要補一輪 smoke 驗證

換句話說，downstream repo 仍然擁有自己的 `tests/**`；core 自己只需要攜帶一套 portable smoke contract。

---

## 6. 完成 subtree sync 前的最低條件

在目前 repo 結構下，至少要同時滿足以下條件，才適合把 curated core 拿去做 subtree transport：

1. `AGENT_ENTRY.md` 依賴的 root live path 已保留，或已有可執行 projection/bootstrap script
2. `.agent/skills/_shared/skill_manifest.json` 不再寫入 core tree
3. `.agent/skills/_shared/skill_whitelist.json` 不再作為 core 內 canonical policy file
4. `.agent/skills/_shared/audit.log` 不再寫入 core tree
5. `.agent/skills/INDEX.md` 不再承擔 local/generated append 責任
6. external/local skills 不再安裝到 `.agent/skills/**`
7. portable smoke suite 的路徑與觸發點已定型，不再依賴 `tests/**` 作為唯一共用驗證入口
8. `workflow-core sync precheck|apply|verify` 與 `workflow-core release precheck` 已約定共讀同一份 `./core_ownership_manifest.yml`

截至 2026-03-19，條件 2 到 6 已落 code；剩餘主要是條件 1、7、8 的 delivery / verification contract 持續收斂。

若第 1 項沒完成，subtree 會先破壞 workflow 入口；若第 2 到 6 項沒完成，就算 manifest 已寫好，也只是在把 mutable 路徑包進 subtree 衝突裡。

---

## 7. 最短結論

目前真正阻止 subtree 落地的，不是 git subtree 本身，而是 `.agent/skills` 仍同時扮演：

- core package tree
- local install tree
- runtime metadata store
- project-local policy store
- generated audit/index output

同時，`AGENT_ENTRY.md` 與其下游 workflow/role docs 仍把 root 下 `./.agent/**` 與 `./doc/**` 當成 live contract。

所以 subtree sync 前的正確動作，不是先 export，也不是先搬 `.agent/workflows/**`；而是先保住 live path，再把 `.agent/skills` 這五種責任拆開。
