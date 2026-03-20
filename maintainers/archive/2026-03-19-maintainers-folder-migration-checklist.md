# Maintainers Folder 搬遷紀錄

> 建立日期：2026-03-19
> 狀態：Archived - completed migration record
> 目的：記錄 `doc/maintainers/` 移到 repo root `maintainers/` 前後的受影響文件、規則與下游交付判定，避免搬遷過程中遺漏 active 導航或 export contract。

> 補充：本文件內提及 GitHub template 的段落，僅作歷史脈絡與交付決策分析，不是現行推薦路徑。

---

## 0. 先講結論

### 0.1 `maintainers/` 是否屬於下游新專案必需內容

結論：**不是**。

依目前 repo 內既有契約，`maintainers/**` 的定位已經是 template maintainer only，不是下游專案的 active workflow 文檔面。

已確認的證據：

1. `core_ownership_manifest.yml` 已把 `maintainers/**` 列為 `never-export`
2. `maintainers/index.md` 明講這份索引只用於維護 `agent-workflow-template` 本身
3. `maintainers/chat/README.md` 明講這些文件不是下游專案模板內容
4. `.agent/PORTABLE_WORKFLOW.md` 的移植清單沒有要求複製 `maintainers/`

### 0.2 用這個 template 建立新專案時，`maintainers/` 目前會不會跟著進新 repo

要分成三條交付路徑看：

1. **GitHub `Use this template` 路徑**
   - 會。
   - 原因不是它應該進去，而是 GitHub template 會直接複製整個 repository 內容；目前 repo 內沒有額外的 post-create prune 機制去自動刪掉 `maintainers/`。

2. **Portable/setup script 路徑**
   - 不會。
   - `.agent/PORTABLE_WORKFLOW.md` 與 `setup_workflow.sh` 的複製清單本來就沒有包含 `maintainers/`。

3. **core + overlay + subtree/export 路徑**
   - 不應該。
   - `core_ownership_manifest.yml` 已把 `maintainers/**` 列為 `never-export`。

### 0.3 因此這次搬遷決策真正要解的是什麼

若你的目標是：

- 讓 `/doc` 只保留下游專案真的會用到的文件
- 讓 maintainer-only 文檔從資訊架構上退出 `/doc`

那麼把原本的 `doc/maintainers/` 搬到 repo root 的 `maintainers/` 是合理方向。

但若你的目標更進一步是：

- **GitHub `Use this template` 建新 repo 時，也不要把 maintainer 文件一起帶進去**

那麼「只搬路徑」**還不夠**。因為只要 maintainer 文件仍在同一個 template repository 裡，不管它在 `maintainers/` 還是 `maintainers/`，GitHub template 都一樣會整包複製。

這代表要達成「GitHub template 新 repo 不含 maintainer 文件」，還需要額外二選一：

1. 改成由 export/setup flow 產生下游專案，而不是直接用 GitHub template 全 repo 複製
2. 或建立一個專門給 downstream 使用的精簡 template surface，把 maintainer 文件留在上游維護來源，不直接暴露在 template repo 中

---

## 1. 搬遷目標

本清單以下都以這個已採用方向為準：

- **來源路徑**：`doc/maintainers/`（歷史來源）
- **目標路徑**：`maintainers/`

選 `maintainers/` 而不是 `.maintainers/` 的理由：

1. 這些不是 runtime state，也不是暫存產物
2. 這些文件需要被 maintainer 主動閱讀、搜尋、連結
3. 放在 repo root 的可見度比 hidden directory 更合理

### 1.1 完成狀態

1. 已完成：實體路徑由 `doc/maintainers/` 移到 repo root `maintainers/`
2. 已完成：active docs 與 machine-readable contract 的主要引用已切到 `maintainers/`
3. 已完成：archive 歷史文檔的相對連結驗證與補修
4. 已完成：repo 全域 markdown 連結與 editor errors 複驗通過

---

## 2. 規則層修改紀錄

### 2.1 Machine-readable contract

這些檔案不只影響連結，也影響「哪些路徑算 downstream 不應交付」的機器可讀規則。

1. `core_ownership_manifest.yml`
   - 已切到：`maintainers/**`
   - 影響：subtree/export exclusion、後續 wrapper command 契約說明、人工治理一致性

2. `maintainers/chat/2026-03-19-core-ownership-manifest-v1.md`
   - 目前是 machine-readable manifest 的人類可讀說明鏡像
   - 已同步改成 `maintainers/**`

### 2.2 Ignore / local export rules

1. `.gitignore`
   - 已切到：`maintainers/chat/*.json`
   - 否則 chat export JSON 會開始被 git 看見

### 2.3 文件面 contract

若 `/doc` 的目標是只保留下游專案會用到的文檔，則以下原則也要一起固定：

1. `/doc` 保留：
   - `doc/plans/**`
   - `doc/logs/**`
   - `doc/implementation_plan_index.md`
   - `doc/NEW_MACHINE_SETUP.md`
   - `doc/ENVIRONMENT_RECOVERY.md`
   - `doc/HOME_OFFICE_SWITCH_SOP.md`
   - 其他下游專案會直接用到的操作文檔

2. `maintainers/` 承接：
   - chat handoff / archive / governance
   - terminal tooling source-map
   - devcontainer maintainer notes
   - template 自我維護 closure / archive

3. 若 `doc/NEW_MACHINE_SETUP.md`、`doc/ENVIRONMENT_RECOVERY.md`、`doc/HOME_OFFICE_SWITCH_SOP.md` 要繼續保留在 `/doc`
   - 它們仍可連到 `maintainers/`
   - 但語氣要更明確標示「這段是 template maintainer 操作，不是下游專案必要內容」

---

## 3. 搬遷影響清單

以下清單來自搬遷前的 workspace 全域字串盤點，用來記錄這次從 `doc/maintainers/` 遷出時需要一起修的檔案範圍。其用途是保留搬遷影響面，不代表這些檔案現在仍未處理。

### 3.1 Repo root / 外部入口

1. `README.md`
   - 兩類變更都要做：
   - `maintainers/chat/*.json` / `handoff/` 路徑改寫
   - `maintainers/index.md` 導航入口改寫
   - 補充說明：若未來仍保留 GitHub template 路線，README 還應明講 maintainer 文件目前會跟著 template 一起複製

2. `.gitignore`
   - chat JSON ignore 路徑改寫

3. `core_ownership_manifest.yml`
   - excluded path 改寫

### 3.2 下游仍可能閱讀的操作文件

1. `doc/NEW_MACHINE_SETUP.md`
   - `maintainers/devcontainer_modes.md`
   - `maintainers/chat/handoff/`
   - `maintainers/chat/*.json`
   - `maintainers/chat/README.md`
   - 全數需改路徑

2. `doc/ENVIRONMENT_RECOVERY.md`
   - `maintainers/chat/handoff/`
   - `maintainers/chat/*.json`
   - `maintainers/`
   - 全數需改路徑與描述文字

3. `doc/HOME_OFFICE_SWITCH_SOP.md`
   - `maintainers/chat/`
   - `maintainers/chat/handoff/SESSION-HANDOFF.template.md`
   - `maintainers/chat/README.md`
   - 全數需改路徑

### 3.3 Runtime / tooling README 中的 maintainer 導航入口

1. `.agent/runtime/tools/vscode_terminal_pty/README.md`
   - 目前連到 `maintainers/chat/2026-03-19-terminal-tooling-source-map.md`
   - 搬遷後需改成 `maintainers/chat/2026-03-19-terminal-tooling-source-map.md`

### 3.4 Active maintainer indexes / governance docs

1. `maintainers/index.md`
   - 已完成移動到 repo root
   - 內部所有相對路徑需重算
   - 例如 `../NEW_MACHINE_SETUP.md` 類型的相對路徑將不再成立

2. `maintainers/chat/README.md`
   - 內文大量寫死 `maintainers/...`
   - 搬遷後需整批改寫為 `maintainers/...`

3. `maintainers/archive/README.md`
   - 內文有 `maintainers/archive/` 與 `maintainers/chat/archive/` 路徑說明
   - 搬遷後需同步改寫

4. `maintainers/chat/2026-03-19-core-ownership-manifest-v1.md`
   - 規則鏡像，需要同步 excluded path

5. `maintainers/chat/2026-03-19-terminal-tooling-source-map.md`
   - active maintainer 導航文，內部 archive 路徑需整批改寫

### 3.5 Archive / history 文件

這些檔案不一定承擔現行規則，但若真的搬遷資料夾，連結仍會壞掉，因此要一起改。

#### `maintainers/archive/`

1. `maintainers/archive/2026-03-16-copilot-cli-migration-checklist.md`
2. `maintainers/archive/2026-03-18-workflow-optimization-plan.md`
3. `maintainers/archive/README.md`

#### `maintainers/chat/archive/`

1. `maintainers/chat/archive/2026-03-12-dual-pty-followup-handoff.md`
2. `maintainers/chat/archive/2026-03-13-legacy-terminal-pre-delete-checklist.md`
3. `maintainers/chat/archive/2026-03-13-merged-fallback-tool-draft-lineage.md`
4. `maintainers/chat/archive/2026-03-13-merged-fallback-tool-spec.md`
5. `maintainers/chat/archive/2026-03-13-pre-rebuild-handoff.md`
6. `maintainers/chat/archive/2026-03-13-preflight-migration-plan.md`
7. `maintainers/chat/archive/2026-03-13-pty-monitor-and-capture-contract.md`
8. `maintainers/chat/archive/2026-03-13-pty-status-summary-and-next-steps.md`
9. `maintainers/chat/archive/2026-03-13-pty-workflow-readiness-handoff.md`
10. `maintainers/chat/archive/2026-03-13-terminal-pty-next-step-handoff.md`
11. `maintainers/chat/archive/2026-03-13-terminal-pty-target-architecture-and-migration-principles.md`
12. `maintainers/chat/archive/2026-03-13-workflow-structure-analysis-handoff.md`
13. `maintainers/chat/archive/2026-03-17-dev-workflow-current-flow-and-optimization-map.md`
14. `maintainers/chat/archive/2026-03-18-workflow-optimization-handoff.md`
15. `maintainers/chat/archive/2026-03-19-terminal-tooling-archive-checklist.md`
16. `maintainers/chat/archive/README.md`

### 3.6 本次新增的 migration checklist 本身

1. `maintainers/chat/handoff/2026-03-19-maintainers-folder-migration-checklist.md`
   - 已隨本次搬遷一起移到 repo root `maintainers/`

---

## 4. 搬遷執行順序紀錄

### Phase 1. 固定決策

先回答兩個問題：

1. 目標只是讓 `/doc` 更乾淨，還是要讓 GitHub template 建新 repo 時不再包含 maintainer 文件
2. 新路徑是否採用 `maintainers/` repo root

若第 1 題答案是「連 GitHub template 下游 repo 也不要帶 maintainer 文件」，那就不能只做路徑搬遷，還要改交付模式。

### Phase 2. 路徑搬遷與連結改寫

1. 實際移動整個 `doc/maintainers/` 到 `maintainers/`
2. 先改 machine-readable contract：
   - `core_ownership_manifest.yml`
   - human-readable mirror
   - `.gitignore`
3. 再改 repo 外圍導航：
   - `README.md`
   - `doc/NEW_MACHINE_SETUP.md`
   - `doc/ENVIRONMENT_RECOVERY.md`
   - `doc/HOME_OFFICE_SWITCH_SOP.md`
   - `.agent/runtime/tools/vscode_terminal_pty/README.md`
4. 最後整批改寫 maintainer 內部自連結與 archive 歷史連結

目前狀態：1-4 已完成。

### Phase 3. 驗證

至少要驗證：

1. 全 repo 不應再殘留 `doc/maintainers` 活動路徑引用
2. `maintainers/chat/README.md`、`maintainers/index.md` 內所有相對連結可正常打開
3. `README.md` 導航仍能通到 maintainer 文件
4. `core_ownership_manifest.yml` 的 excluded path 已與新路徑一致
5. `.gitignore` 仍能忽略 maintainer chat JSON

驗證結果：以上項目均已完成；目前 repo 中殘留的 `doc/maintainers` 字樣只保留於本紀錄作為歷史來源描述。

---

## 5. 若目標是「GitHub template 新 repo 不要含 maintainer 文件」，還要再補什麼

這是和單純搬路徑不同的第二層決策。

### 方案 A：保留目前 repo 作為 maintainer source，不再把它直接當 downstream template surface

做法：

1. maintainer source repo 保留完整治理文件
2. 由 export/setup flow 產生下游 repo surface
3. downstream 只吃 curated core + overlay 初始化內容

優點：

1. 最符合 `core_ownership_manifest.yml` 現有方向
2. maintainer 文件天然不會進下游

代價：

1. 不再是單純點 GitHub `Use this template` 就結束

### 方案 B：仍保留 GitHub template，但明確接受 maintainer 文件會先被複製，再由 bootstrap 清掉

做法：

1. README 明講 maintainer 文件是 template-only
2. 在新 repo 初始化步驟加入刪除或搬離 maintainer 文件

優點：

1. 仍可繼續用 GitHub template

代價：

1. maintainer 文件仍會先進 repo，再靠人或腳本清除
2. 容易因漏做清理而殘留

### 方案 C：拆成兩個 repo / 兩個 branch surface

做法：

1. 一個維護來源含 maintainer 文檔
2. 一個專門給 downstream `Use this template`

優點：

1. GitHub template 使用體驗最好

代價：

1. 維護成本最高
2. 兩個 surface 容易漂移

---

## 6. 決策結論

1. 若目標只是清理 `/doc` 的資訊架構，搬到 `maintainers/` 是正確且已執行的方向
2. 若目標還包含「GitHub template 新 repo 不帶 maintainer 文件」，則仍需另外調整 downstream 交付模式
3. 因此本次搬遷完成後，後續真正待決的是交付模型，而不是 maintainer 路徑本身

---

## 7. 最短判定

已開始搬，而且從資訊架構上**應該搬**。

但要先分清楚兩件不同的事：

1. **路徑整理**：把 maintainer-only 文檔從 `/doc` 拿出去
2. **下游交付隔離**：讓 GitHub template 新 repo 不再含 maintainer-only 文檔

第 1 件只要改路徑與連結。

第 2 件單靠改路徑做不到，因為 GitHub template 會複製整個 repo。
