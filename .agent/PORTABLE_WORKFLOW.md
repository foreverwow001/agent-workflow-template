# 🚀 Portable Workflow Guide

> 本文件說明如何將此 Workflow 系統移植到其他專案。

> 這份文件現在也是唯一推薦的 downstream bootstrap 入口。GitHub `Use this template` 不再是推薦的下游建專案方式，因為它會複製整個 repository，而不是只交付 curated core surface。

---

## 📦 必須移植的檔案結構

```
new-project/
├── .agent/
│   ├── workflow_baseline_rules.md  📌 僅 template repo 維護使用；下游專案可移除
│   ├── workflows/
│   │   ├── AGENT_ENTRY.md       ✅ 核心入口（通用）
│   │   └── dev-team.md          ✅ 團隊流程（通用）
│   ├── roles/
│   │   ├── planner.md           ✅ 規劃師（通用）
│   │   ├── engineer.md          ✅ 工程師（通用）
│   │   ├── engineer_pending_review_recorder.md  ✅ 工程 triage 記錄 overlay（通用）
│   │   ├── qa.md                ✅ 品管員（通用）
│   │   ├── qa_pending_review_recorder.md        ✅ QA triage 記錄 overlay（通用）
│   │   ├── domain_expert.md     ⚙️ 領域專家（需客製）
│   │   ├── security.md          ✅ 安全審查員（通用）
│   │   └── security_pending_review_recorder.md  ✅ 安全 triage 記錄 overlay（通用）
│   ├── skills/
│   │   ├── INDEX.md             ✅ 技能索引（通用）
│   │   ├── code-reviewer/       ✅ 代碼審查 skill package（通用）
│   │   ├── doc-generator/       ✅ 文件生成 skill package（通用）
│   │   ├── test-runner/         ✅ 測試執行 skill package（通用）
│   │   ├── plan-validator/      ✅ Plan 驗證 skill package（通用）
│   │   ├── git-stats-reporter/  ✅ Git 統計 skill package（通用）
│   │   ├── skills-evaluator/    ✅ 技能統計 skill package（通用）
│   │   ├── github-explorer/     ✅ 外部技能搜尋/下載 package（通用）
│   │   ├── skill-converter/     ✅ 外部技能轉換 package（內部 toolchain）
│   │   ├── manifest-updater/    ✅ manifest 同步 package（通用）
│   │   ├── pending-review-recorder/ ✅ triage 記錄與 dedupe 規格（通用）
│   │   ├── _shared/             ✅ shared helper / path resolver
│   │   ├── explore-cli-tool/    ✅ CLI 探索（通用）
│   │   └── schemas/             ✅ output schema public path
│   ├── skills_local/            🔄 external/local skills install target
│   ├── state/skills/INDEX.local.md  🔄 local overlay skill catalog
│   ├── templates/
│   │   └── handoff_template.md  ✅ 交接模板（通用）
│   └── active_sessions.json     🔄 執行時生成
├── project_maintainers/
│   ├── chat/
│   │   ├── README.md            ✅ downstream project handoff guidance
│   │   ├── handoff/
│   │   │   └── SESSION-HANDOFF.template.md  ✅ downstream session handoff 模板
│   │   └── archive/
│   │       └── README.md        ✅ downstream handoff archive guide
│   └── improvement_candidates/
│       ├── README.md            ✅ downstream candidate queue 說明
│       ├── IMPROVEMENT-CANDIDATE.template.md  ✅ candidate 模板
│       └── PROMOTION-GUIDE.md   ✅ promotion criteria 與 decision rules
├── doc/
│   ├── plans/
│   │   └── Idx-000_plan.template.md  ✅ Plan 模板
│   └── implementation_plan_index.md  🆕 需新建
└── project_rules.md             ⚙️ 下游專案 active 規則檔（取代 ivy_house_rules.md）
```

> template repo 自身維護時，`READ_BACK_REPORT` 應讀 `./.agent/workflow_baseline_rules.md`；移植到新專案後，active rule source 改為根目錄 `project_rules.md`。

---

## 🔧 移植步驟

這套流程對應的是目前已定下的 core + overlay 模型：

1. 第一次把 curated workflow core materialize 到下游 repo
2. 讓下游專案自己的規則、plans、logs 與 domain overlay 留在 managed paths 之外
3. 後續更新改走 `workflow-core release/*` 與 `workflow-core sync/*`，而不是再次整包複製 template repo

技能系統的 split contract 也已定型：builtin core catalog 保留在 `.agent/skills/INDEX.md`，external/local skills 安裝到 `.agent/skills_local/`，overlay catalog 則寫到 `.agent/state/skills/INDEX.local.md`。

另外，curated core 現在也會帶出 `project_maintainers/chat/` 與 `project_maintainers/improvement_candidates/` skeleton，讓新專案一開始就具備自己的 handoff / archive / candidate 落點。這組 skeleton 是 downstream project-local supporting surface，不是 authoritative workflow 規則來源。

### Step 0: 先確認最小依賴

下游 repo 最小建議依賴如下：

- `git`
- `python` 或 `python3`，且必須支援 `venv`
- `node`
- `npm`
- `codex`
- `copilot`
- `bwrap`（Linux / Dev Container 環境建議安裝）

若你是用目前這份 curated core 啟動新 repo，建議先跑：

```bash
bash .agent/runtime/scripts/install_workflow_prereqs.sh
```

這支腳本會先檢查上述依賴；若環境具備 `apt-get` 與可用的 root / passwordless `sudo`，或具備可寫的 global npm prefix，則會自動安裝缺少的項目。

若你只想檢查、不想安裝：

```bash
bash .agent/runtime/scripts/install_workflow_prereqs.sh --check-only
```

### Step 1: 複製核心檔案

```bash
# 設定來源與目標
SOURCE="/workspaces/ivyhousetw ad analyzer/Ivyhousetw-META"
TARGET="/path/to/new-project"

# 複製 .agent 目錄
cp -r "$SOURCE/.agent" "$TARGET/"

# 複製 doc 模板
mkdir -p "$TARGET/doc/plans"
mkdir -p "$TARGET/doc/logs"
cp "$SOURCE/doc/plans/Idx-000_plan.template.md" "$TARGET/doc/plans/" 2>/dev/null || echo "模板不存在，稍後建立"
cp "$SOURCE/doc/logs/Idx-000_log.template.md" "$TARGET/doc/logs/" 2>/dev/null || echo "Log 模板不存在，稍後建立"
```

### Step 2: 建立專案規則檔

建立 `project_rules.md`（取代 `ivy_house_rules.md`），包含：

```markdown
# [專案名稱] - 系統開發核心守則

## 1. 核心溝通規範
- 語言：繁體中文 / English
- 確認機制：執行前必須複述需求

## 2. 架構策略
- [依專案調整]

## 3. 開發流程
- Git Flow: [依專案調整]

## 4. 技術規範
- 檔案長度：主程式 ≤ 600 行
- [其他規範]

## 5. 資安紅線
- 絕對禁止 Hard-code API Key
```

### Step 3: 更新 AGENT_ENTRY.md 必讀清單

確認 `.agent/workflows/AGENT_ENTRY.md` 在下游專案中以 `project_rules.md` 作為 active rule source；template repo 維護時才讀 `./.agent/workflow_baseline_rules.md`。

```markdown
## 1) 必讀檔案
1. `./.agent/workflows/dev-team.md`
2. `./project_rules.md`              ← 下游專案的 active 規則檔
3. `./doc/implementation_plan_index.md`
```

### Step 4: 客製化領域專家角色

編輯 `domain_expert.md` 成為專案適用的領域專家：

| 專案類型 | 領域專家角色 |
|---------|-------------|
| Meta 廣告分析 | Domain Expert（數據計算） |
| 電商系統 | E-commerce Expert (訂單/庫存) |
| 金融系統 | Finance Expert (合規/計算) |
| API 開發 | API Expert (設計/安全) |

### Step 5: 保留安全審查員角色

`security.md` 應作為通用角色一起移植，用於條件式安全審查，不需要依專案類型重寫結構，只需補充專案特有的高風險面。

### Step 5: 初始化 Index

建立空的 `doc/implementation_plan_index.md`：

```markdown
# Implementation Plan Index

| Task ID | 名稱 | 狀態 | 建立日期 | 完成日期 |
|---------|------|------|---------|---------|
| Idx-001 | [首個任務] | Planning | YYYY-MM-DD | - |
```

---

## 🔄 快速移植腳本

```bash
#!/bin/bash
# setup_workflow.sh - 快速初始化 Agent Workflow

set -e

# 檢查參數
if [ -z "$1" ]; then
    echo "用法: ./setup_workflow.sh /path/to/new-project"
    exit 1
fi

TARGET="$1"
SOURCE="$(dirname "$0")/.."

echo "🚀 初始化 Agent Workflow..."

# 建立目錄結構
mkdir -p "$TARGET/.agent/workflows"
mkdir -p "$TARGET/.agent/roles"
mkdir -p "$TARGET/.agent/skills"
mkdir -p "$TARGET/.agent/skills_local"
mkdir -p "$TARGET/.agent/templates"
mkdir -p "$TARGET/doc/plans"

# 複製通用檔案
cp "$SOURCE/.agent/workflows/AGENT_ENTRY.md" "$TARGET/.agent/workflows/"
cp "$SOURCE/.agent/workflows/dev-team.md" "$TARGET/.agent/workflows/"
cp "$SOURCE/.agent/roles/planner.md" "$TARGET/.agent/roles/"
cp "$SOURCE/.agent/roles/engineer.md" "$TARGET/.agent/roles/"
cp "$SOURCE/.agent/roles/qa.md" "$TARGET/.agent/roles/"
cp -r "$SOURCE/.agent/skills/code-reviewer" "$TARGET/.agent/skills/"
cp -r "$SOURCE/.agent/skills/doc-generator" "$TARGET/.agent/skills/"
cp -r "$SOURCE/.agent/skills/test-runner" "$TARGET/.agent/skills/"
cp -r "$SOURCE/.agent/skills/plan-validator" "$TARGET/.agent/skills/"
cp -r "$SOURCE/.agent/skills/git-stats-reporter" "$TARGET/.agent/skills/"
cp -r "$SOURCE/.agent/skills/skills-evaluator" "$TARGET/.agent/skills/"
cp "$SOURCE/.agent/skills/INDEX.md" "$TARGET/.agent/skills/"
cp "$SOURCE/.agent/templates/handoff_template.md" "$TARGET/.agent/templates/"

# 建立空的 active_sessions.json
echo '{"sessions": []}' > "$TARGET/.agent/active_sessions.json"

# 建立空的 Index
cat > "$TARGET/doc/implementation_plan_index.md" << 'EOF'
# Implementation Plan Index

| Task ID | 名稱 | 狀態 | 建立日期 | 完成日期 |
|---------|------|------|---------|---------|
| - | - | - | - | - |
EOF

echo "✅ Workflow 初始化完成！"
echo "📝 請記得："
echo "   1. 建立 project_rules.md"
echo "   2. 確認下游專案以 project_rules.md 作為 active rule source"
echo "   3. 客製化領域專家角色"
```

---

## 📋 移植 Checklist

- [ ] 複製 `.agent/` 目錄
- [ ] 建立 `project_rules.md`（專案規則）
- [ ] 確認 `AGENT_ENTRY.md` 在下游專案讀 `project_rules.md`
- [ ] 客製化領域專家角色
- [ ] 建立 `doc/implementation_plan_index.md`
- [ ] 建立 `doc/plans/` 目錄
- [ ] 測試：執行 `/dev`（或 `/dev-team`）確認流程正常

---

## 🎯 為什麼不再推薦 GitHub Template

1. GitHub `Use this template` 會直接複製整個 repository
2. 它無法遵守 `core_ownership_manifest.yml` 中已定下的 curated export boundary
3. 它會把 maintainer-only、template-only、mutable/generated surface 一起帶進下游 repo
4. 它也無法提供後續 upstream core sync 的固定 contract

因此，GitHub template 最多只適合作為歷史或過渡方案，不再是正式推薦的 downstream 建專案方式。

---

## ⚠️ 注意事項

1. **規則檔分工**：template repo 維護讀 `.agent/workflow_baseline_rules.md`；下游專案讀 `project_rules.md`
2. **領域專家**：`domain_expert.md` 需依專案客製
3. **安全審查**：`security.md` 作為通用角色一併保留
3. **技能擴充**：新專案可能需要新增專用技能
4. **Index 獨立**：每個專案有自己的 `implementation_plan_index.md`
