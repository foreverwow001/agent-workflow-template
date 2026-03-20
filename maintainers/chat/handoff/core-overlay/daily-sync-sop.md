# Core + Overlay 日常同步 SOP

> 建立日期：2026-03-19
> 狀態：Active Maintainer SOP
> 用途：定義 core + overlay 分層搭配 git subtree 後，日常如何做 upstream 發版到 downstream 同步，以及在 downstream 開發中遇到 workflow friction 時應如何分流處理。

---

## 0. 這份 SOP 的適用前提

這份 SOP 只在以下前提成立後才有效：

1. core ownership boundary 已定義完成
2. `.agent/skills` 的 mutable state 已從 subtree-managed core 拆出
3. `AGENT_ENTRY.md` 依賴的 root live path 已保留，或已有 projection/bootstrap 機制可重建

若以上任一條件未完成，請先回到：

- `2026-03-19-core-ownership-manifest-v1.md`
- `2026-03-19-subtree-mutable-path-split-checklist.md`

這份 SOP 不處理「怎麼做第一次拆分」，只處理拆分後的日常運作。

若要把這份 SOP 進一步落成 wrapper command / release gate，請接著看：

- `sync-checklist.md`

---

## 1. 先固定兩條 lane

日常操作一律先判斷要走哪一條 lane，不要混用：

### Lane A. Upstream Improvement -> Downstream Sync

適用情境：

- 你優化了共通 workflow 能力
- 你新增了應該讓所有專案共用的 template 功能
- 你修掉了多個專案都可能踩到的共通 friction

核心原則：

- 改 upstream core 一次
- 用 subtree 把變更同步到 downstream
- downstream 不長期持有 core managed paths 的私人 fork

### Lane B. Downstream Friction Triage

適用情境：

- 你在某個實際專案中使用 workflow 時遇到 friction
- 你不確定這個問題是 project-local 還是應該回 upstream
- 你需要先止血，再決定正式落點

核心原則：

- 先分類 friction，再決定修改位置
- project-local 留在 overlay
- 共通問題修 upstream
- runtime state / generated output 不得回流進 core

---

## 2. Lane A: 上游發版到下游同步的標準步驟

### A-1. 在 upstream 先判斷這次改動是否屬於 core

符合以下條件，才應進 upstream core：

- 是可攜的共通 workflow 能力
- 不是單一專案才需要的 policy 或整合
- 不會把 project-local config、runtime state 或 generated output 重新塞回 core

若不符合，改 overlay，不要假借「模板優化」名義把專案特例送回 core。

### A-2. 在 upstream 完成實作

實作時遵守三個限制：

1. 只修改 `managed_paths` 內應由 core 擁有的內容
2. 不直接把 mutable state 再放回 `.agent/skills` core tree
3. 不破壞 root live path contract

如果這次改動碰到 ownership 邊界、live path contract、skills state split，先補文件再合程式：

- `core_ownership_manifest.yml` 對應欄位
- mutable split checklist
- 任何新的 projection/bootstrap 規格

### A-3. 在 upstream 做 release-ready 驗證

至少確認下面四件事：

1. `AGENT_ENTRY.md` 入口仍可成立
2. preflight / bootstrap 路徑沒有被破壞
3. `.agent/skills` 沒有重新出現 runtime-written diff source
4. 這次改動沒有把 downstream overlay 應持有的責任吸回 core

### A-4. 產生可同步的 upstream release reference

每次要給 downstream 同步前，至少保留一個明確 release ref：

- tag
- release branch ref
- 或固定 commit SHA

不要只說「同步最新 main」，否則 downstream 無法追蹤自己目前吃到哪一版 core。

### A-5. 在 downstream 同步前先做 dirty-state 檢查

downstream 在 pull subtree 前，先看本地變更屬於哪一類：

1. overlay path 變更：可保留
2. state/generated path 變更：可保留，但不應進 core sync review
3. core managed path 變更：先停下，判斷這是不是不該存在的 local fork

若 downstream 已直接修改 core managed paths，不要直接硬拉 subtree 更新。先做分類：

- 若這個修改應該成為共通能力：先回 upstream
- 若只是專案特例：搬出 core managed path，改放 overlay

### A-6. 執行 downstream subtree 同步

實際同步方式，以你最後採用的 delivery mode 為準：

- 若 core 直接 materialize 在 root live path：更新 subtree 後直接覆蓋對應 managed paths
- 若 core 先同步到 staging/export 區：更新 subtree 後必須再跑 projection/bootstrap，把內容投影回 root live path

這一步的重點不是 raw `git subtree` 指令長相，而是一定要固定成同一條團隊可重複執行的 sync command wrapper。不要讓每個 downstream 專案各自手打不同 subtree 指令。

### A-7. 同步後立刻跑最小驗證

downstream 至少要驗證：

1. `AGENT_ENTRY.md` 要求的必讀 live path 仍存在
2. workflow preflight 可通過
3. 一次最小 smoke flow 可成立
4. 專案自己的 overlay config 仍然有效

若同步後壞的是 root live path、projection、或 `.agent/skills` split contract，這不是單一專案問題，應回 upstream 修。

### A-8. 記錄 downstream 目前跟到哪個 upstream ref

每個 downstream 專案都應記錄：

- sync 日期
- upstream ref
- 是否有 projection/bootstrap 後處理
- 是否有 local divergence 尚未清掉

沒有這層記錄，後續 friction 很容易變成「不知道是上游 bug、同步失敗、還是本地分叉」。

---

## 3. Lane B: 開發中遇到 friction 時的 decision tree

遇到 friction 時，先按下面順序判斷。

### Step 1. 先問：這是 root live path / projection 問題嗎？

判定特徵：

- `AGENT_ENTRY.md` 找不到應讀檔案
- root 下 `./.agent/**` 或 `./doc/**` live path 缺失
- subtree 更新後需要手動改入口文件才勉強能跑

若是：

- 不要在 downstream 直接 patch 入口文件當成長期解法
- 這屬於 core delivery contract 問題
- 走 upstream 修正 projection/bootstrap 或 delivery mode

### Step 2. 再問：這是 `.agent/skills` mutable/state 污染問題嗎？

判定特徵：

- sync 後反覆出現 `skill_manifest.json`、`skill_whitelist.json`、`audit.log`、`INDEX.md` 衝突
- local/external skills 與 builtin core skills 混在一起
- 正常使用 workflow 就把 core tree 弄 dirty

若是：

- 不要把它當成單次 merge conflict 解
- 這屬於 mutable path split 問題
- 回 upstream 修 path split / ownership boundary

### Step 3. 再問：這是 project-local policy 或整合需求嗎？

判定特徵：

- 只影響單一專案
- 跟該專案的 repo 規範、部署流程、團隊政策、白名單或本地 skill 使用方式有關

若是：

- 留在 overlay
- 不要回 upstream
- 也不要佔用 core managed path

### Step 4. 再問：這是可攜的共通 workflow friction 嗎？

判定特徵：

- 下一個新專案大機率也會遇到
- 問題存在於流程設計、共用 skill、runtime、preflight 或共通文件 contract

若是：

- 走 upstream 修正
- 修完後發一個可追蹤 ref
- 再回目前專案做 subtree sync

### Step 5. 若現在有 blocker，先決定能不能做短期止血

只在以下條件下允許暫時性 downstream 修補：

1. 你當下必須先讓專案繼續開發
2. 正式 upstream 修復來不及在同一輪完成
3. 你能清楚標記這是一個 temporary divergence

短期止血規則：

- 優先放 overlay
- 若真的不得不碰 core managed path，必須立刻建立 upstream follow-up
- 下一次吃到 upstream 正式修復後，必須把 temporary divergence 清掉

---

## 4. 一張最短 decision tree

1. 入口或 live path 壞了？
   - 是：upstream 修 delivery contract，不留 downstream 永久 patch
2. `.agent/skills` 又開始產生 mutable/state 衝突？
   - 是：upstream 修 split / ownership，不把它當單次 merge conflict
3. 只跟這個專案的 policy、白名單、整合有關？
   - 是：留 overlay，不進 core
4. 下一個專案也會受益？
   - 是：修 upstream core，再 subtree sync 回來
5. 現在非止血不可？
   - 是：先做 temporary downstream patch，但要立刻排 upstream 收斂

---

## 5. 兩條 lane 的日常操作守則

### Do

- 把共通能力修在 upstream
- 把專案特例留在 overlay
- 每次 downstream sync 都記錄 upstream ref
- 每次 sync 後都驗證 live path、preflight、smoke flow
- 把 temporary divergence 視為待清理負債，而不是正常狀態

### Do Not

- 不要把 downstream 專案直接養成 core managed paths 的私人 fork
- 不要把 runtime state、local install、generated output 重新塞回 core
- 不要用手動改 `AGENT_ENTRY.md` 來掩蓋 delivery contract 問題
- 不要把 recurring subtree conflict 當成人工解衝突流程的一部分

---

## 6. 最短結論

日常同步其實只做兩件事：

1. 共通能力走 upstream improvement lane，發版後讓 downstream 用 subtree sync 吃回來
2. 使用中的 friction 先分類，再決定它屬於 overlay、upstream core，還是 delivery/split contract 問題

只要 ownership boundary、live path continuity、`.agent/skills` mutable split 這三件事守住，subtree 才會是低摩擦同步工具；否則它只會把未拆乾淨的責任邊界放大成持續衝突。
