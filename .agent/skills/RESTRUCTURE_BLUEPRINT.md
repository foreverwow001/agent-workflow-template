# Skills 目錄重構藍圖

> 建立日期：2026-03-14
> 狀態：Phase 5 package-only cleanup completed
> 用途：把 `.agent/skills/` 從「平鋪工具箱 + 過渡期 helper 文件」整理成可對齊 Claude / Antigravity skill 結構的目錄藍圖。

---

## 1. 目標

後續 skill 目錄應清楚區分三種東西：

1. **Skill package**
   - 一個 skill 一個資料夾
   - 資料夾內至少有一份 `SKILL.md`
   - 可選 `scripts/`、`REFERENCE.md`、`resources/`
2. **Tool / utility**
   - 可執行腳本或內部轉換器
   - 供 workflow 或 skill package 呼叫
   - 本身不是被模型自動發現的 skill
3. **Shared metadata / governance**
   - manifest、schema、whitelist、索引等
   - 供維護與機械化驗證使用

---

## 2. 目前問題

目前 `.agent/skills/` 已完成 package-only 收斂，核心結構包括：

- 單一索引文件：`INDEX.md`
- 文件型 skill package：`security-review-helper/`、`explore-cli-tool/`、`persistent-terminal/`、`codex-collaboration-bridge/`
- package 內可執行工具：`*/scripts/*.py`
- shared helper / metadata：`_shared/__init__.py`、`.agent/state/skills/skill_manifest.json`、`.agent/config/skills/skill_whitelist.json`、`.agent/state/skills/INDEX.local.md`、`schemas/`

目前結構已符合 Claude / Antigravity 的「一個 skill 一個資料夾」心智模型，後續新增技能應直接沿用 package-only 形式。

---

## 3. 目標結構

```text
.agent/skills/
├── INDEX.md
├── RESTRUCTURE_BLUEPRINT.md
├── _shared/
│   └── __init__.py
├── schemas/
│   └── *_output.schema.json
├── security-review-helper/
│   └── SKILL.md
├── explore-cli-tool/
│   └── SKILL.md
├── persistent-terminal/
│   └── SKILL.md
├── codex-collaboration-bridge/
│   └── SKILL.md
├── code-reviewer/
│   ├── SKILL.md
│   └── scripts/code_reviewer.py
├── plan-validator/
│   ├── SKILL.md
│   └── scripts/plan_validator.py
├── github-explorer/
│   ├── SKILL.md
│   └── scripts/github_explorer.py
├── skill-converter/
│   ├── README.md
│   └── scripts/skill_converter.py
├── manifest-updater/
│   ├── SKILL.md
│   └── scripts/manifest_updater.py
└── ...
```

> 備註：`_shared/` 現在只保留 path resolver 與 shared helper code；runtime state 與 project-local policy 已拆到 `.agent/state/skills/` 與 `.agent/config/skills/`。external/local skills 也已分流到 `.agent/skills_local/`，不再與 builtin core packages 共用 `.agent/skills/`。

---

## 4. 檔案分類決議

### A. 應視為 skill 入口或已完成 package 化的 skill

| 現有檔案 | 建議分類 | 未來位置 | 說明 |
|----------|----------|----------|------|
| `security-review-helper/` | skill package | `security-review-helper/SKILL.md` | 明確的文件型 workflow skill |
| `explore-cli-tool/` | skill package | `explore-cli-tool/SKILL.md` | 明確的 SOP / 文件型 skill |
| `persistent-terminal/` | skill package | `persistent-terminal/SKILL.md` | 長效 session 管理 skill |
| `codex-collaboration-bridge/` | skill package | `codex-collaboration-bridge/SKILL.md` | 特定 workflow 協作 skill |

### B. 應視為工具，不直接當 skill

| 現有檔案 | 建議分類 | 說明 |
|----------|----------|------|
| `code-reviewer/scripts/code_reviewer.py` | tool | 由 `code-reviewer/` skill package 直接呼叫 |
| `doc-generator/scripts/doc_generator.py` | tool | 由 `doc-generator/` skill package 直接呼叫 |
| `test-runner/scripts/test_runner.py` | tool | 由 `test-runner/` skill package 直接呼叫 |
| `plan-validator/scripts/plan_validator.py` | tool | Gate 工具，本身不是文件型 skill 入口 |
| `git-stats-reporter/scripts/git_stats_reporter.py` | tool | Gate / reporting 工具 |
| `skills-evaluator/scripts/skills_evaluator.py` | tool | 後處理與統計工具 |
| `github-explorer/scripts/github_explorer.py` | toolchain | 下載/預覽流程的可執行主體 |
| `skill-converter/scripts/skill_converter.py` | toolchain | 僅供 github_explorer 內部調用 |
| `manifest-updater/scripts/manifest_updater.py` | maintenance tool | 維護 manifest，不應被當成使用者 skill |

### C. 應視為 shared metadata / governance

| 現有檔案 | 建議分類 | 說明 |
|----------|----------|------|
| `.agent/state/skills/skill_manifest.json` | shared metadata | canonical 技能清單索引 |
| `.agent/config/skills/skill_whitelist.json` | governance data | canonical 外部下載來源白名單 |
| `_shared/__init__.py` | shared runtime helper | 路徑常數、package metadata、package 掃描 helper |
| `schemas/` | shared metadata | 維持 public schema path，相容現有 output validator |
| `__init__.py` | shared runtime helper | 動態 AVAILABLE_SKILLS 與 canonical package path 索引 |
| `INDEX.md` | catalog | 這是索引，不是單一 skill |

---

## 5. 重構順序

### Phase 1. 語意先對齊

- [x] `SKILL.md` 改名為 `INDEX.md`
- [x] 明確宣告 `INDEX.md` 只是索引
- [x] 起草本藍圖

### Phase 2. 先搬文件型 skill

優先處理不牽涉執行腳本的 skill：

1. `security-review-helper/`
2. `explore-cli-tool/`
3. `persistent-terminal/`
4. `codex-collaboration-bridge/`

理由：

- 不影響現有 Python 工具路徑
- 最容易對齊 Claude / Antigravity skill 結構

執行結果：

- [x] `security_review_helper.md` → `security-review-helper/SKILL.md`
- [x] `explore_cli_tool.md` → `explore-cli-tool/SKILL.md`
- [x] `persistent_terminal.md` → `persistent-terminal/SKILL.md`
- [x] `use_codex.md` → `codex-collaboration-bridge/SKILL.md`
- [x] repo 內對應引用已切到新 package path

### Phase 3. 再包工具型 skill

對每個工具型能力建立自己的 skill package：

- `code-reviewer/`
- `doc-generator/`
- `test-runner/`
- `plan-validator/`
- `git-stats-reporter/`
- `skills-evaluator/`

每個 package 至少包含：

- `SKILL.md`
- `scripts/<tool>.py` 或對原腳本的穩定引用方式

執行結果：

- [x] `code-reviewer/` canonical package
- [x] `doc-generator/` canonical package
- [x] `test-runner/` canonical package
- [x] `plan-validator/` canonical package
- [x] `git-stats-reporter/` canonical package
- [x] `skills-evaluator/` canonical package
- [x] `manifest-updater/scripts/manifest_updater.py` 已補上 canonical package metadata

### Phase 4. 最後處理剩餘工具鏈與 shared metadata

執行結果：

- [x] `github_explorer.py` → `github-explorer/` canonical package
- [x] `skill_converter.py` → `skill-converter/` canonical package
- [x] `manifest_updater.py` → `manifest-updater/` canonical package
- [x] `skill_manifest.json` / `skill_whitelist.json` 先 canonicalized 到 `_shared/`
- [x] `__init__.py` 改成動態掃描 package 目錄，外部下載技能不再需要手改 registry
- [x] `schemas/` 明確保留在 root public path，由 `_shared` helper 統一路徑存取

### Phase 5. mutable path split（Phase 1）

執行結果：

- [x] manifest canonical write path 改到 `.agent/state/skills/skill_manifest.json`
- [x] whitelist canonical write path 改到 `.agent/config/skills/skill_whitelist.json`
- [x] audit log canonical write path 改到 `.agent/state/skills/audit.log`
- [x] `_shared/` 改為 legacy fallback + path resolver，不再承擔 canonical runtime-written state

### Phase 6. builtin catalog / local overlay split

執行結果：

- [x] `.agent/skills/INDEX.md` 改為 builtin-only core catalog
- [x] local/generated index 改寫到 `.agent/state/skills/INDEX.local.md`
- [x] external/local skill install destination 改到 `.agent/skills_local/**`
- [x] `github-explorer` / `skill-converter` / `__init__.py` 已切到 builtin + local 分流掃描與輸出路徑

---

## 6. 最終策略

- root shim 已移除，所有調用統一使用 `python .agent/skills/<package>/scripts/<tool>.py`
- `schemas/` 不搬進 `_shared/`，避免一次打破所有既有 validator/path 引用
- core `INDEX.md` 維持 stable builtin catalog；local additions 一律寫到 `.agent/state/skills/INDEX.local.md`
- 外部技能下載後改以 `.agent/skills_local/` package 目錄落地，避免重新長回 root `.py` 結構，也避免污染 builtin core package tree

---

## 7. 驗收條件

這份藍圖若要視為可執行，至少要能回答：

1. 哪些檔案是 skill 入口
2. 哪些檔案只是工具
3. 哪些檔案屬於 shared metadata
4. 重構時先搬哪一批、後搬哪一批

目前以上四點都已明確，且 Phase 4 已落地完成，可作為後續只做增量優化的基準。
