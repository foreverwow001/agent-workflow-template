# Core Ownership Manifest V1 草案

> 建立日期：2026-03-19
> 狀態：Active Supporting Doc
> 用途：定義未來 `core_ownership_manifest.yml` 的第一版欄位、格式與目前 repo 的基線內容，作為 subtree sync 前的 ownership baseline。
>
> 這份文件處理的是 **manifest schema + current-repo baseline**，不是實作 patch，也不是正式 archive/retire 決策文。

---

## 1. 這份 manifest 要解決什麼

若後續採用「single source of truth core + downstream overlay + git subtree transport」，就不能只靠口頭約定哪些路徑屬於 core。

先講清楚目前 repo 的兩個硬現實：

1. 最大的 mutable hotspot 是 `.agent/skills`，不是 `.agent/workflows`。
2. 最大的路徑耦合點是 `AGENT_ENTRY.md` 與其下游 workflow/role docs 對 root 下 `./.agent/...`、`./doc/...` live path 的直接假設。

因此 subtree 在這裡只是 transport，不是 runtime path contract 本身。後續若真的拆出 curated core，也不能只把內容放進 `.workflow-core/` 然後期待 repo 自己會 work；不是保留原 live path，就是提供明確 projection/bootstrap script 把 core 重新投影回 root live path。

`core_ownership_manifest.yml` 的角色應固定為：

- 宣告哪些路徑由 core 擁有
- 宣告哪些路徑明確不得進 subtree
- 宣告哪些路徑目前看似屬 core，但在 subtree 前必須先拆出 mutable state
- 讓後續 export branch / sync script / review 都有同一份 machine-readable baseline

第一版還應固定一個實作原則：release / sync automation 的單一 machine-readable source of truth 就是 repo root 的 `./core_ownership_manifest.yml`；`precheck`、`apply`、`verify` 不應各自維護一套 prefix 清單。

---

## 2. V1 設計原則

第一版 manifest 建議只承擔四件事：

1. 描述 core 擁有邊界
2. 描述 exclusion 邊界
3. 描述 pre-sync blocker
4. 描述 downstream edit policy

第一版先不要承擔：

- 自動生成 patch
- 自動移動檔案
- 自動做 subtree push/pull
- 複雜 inheritance 或多層 profile

V1 先求 ownership truth 單一化，不求功能過重。

---

## 3. 建議欄位

第一版 `core_ownership_manifest.yml` 建議至少包含以下頂層欄位：

### A. 基本識別

- `manifest_version`
- `core_id`
- `baseline_repo`
- `baseline_ref`
- `generated_from`

用途：標示這份 manifest 是從哪個 repo / branch / baseline 狀態推導出來。

### B. 策略欄位

- `strategy.source_of_truth`
- `strategy.transport`
- `strategy.export_model`
- `strategy.downstream_default`

建議固定語意：

- `source_of_truth`: `curated-exported-core`
- `transport`: `git-subtree`
- `export_model`: `export-branch-or-export-tree`
- `downstream_default`: `overlay-outside-managed-paths-only`

### C. Root Path Contract

- `root_path_contract.required_live_paths`
- `root_path_contract.required_live_prefixes`
- `root_path_contract.delivery_mode`
- `root_path_contract.projection_strategy`
- `root_path_contract.projection_script`
- `root_path_contract.blocking_assumptions`
- `root_path_contract.notes`

用途：把目前 workflow 對 root live path 的假設明確寫進 manifest，避免後續 subtree 後還以為可以任意改 prefix。

### D. Migration Constraints

- `migration_constraints.primary_mutable_hotspot`
- `migration_constraints.do_not_optimize_first`
- `migration_constraints.primary_path_coupling`
- `migration_constraints.subtree_role`
- `migration_constraints.required_before_transport`

用途：把目前最容易做錯優先順序的現實限制寫死，避免後續 rollout 把時間花在次要路徑，或誤以為 subtree 本身會解決 live path 問題。

### E. Managed Paths

- `managed_paths[]`
  - `path`
  - `kind`
  - `ownership`
  - `sync_policy`
  - `downstream_edit_policy`
  - `reason`

建議語意：

- `ownership`: `core`
- `sync_policy`: `subtree-managed`
- `downstream_edit_policy`: `upstream-only` 或 `local-append-only`

### F. Excluded Paths

- `excluded_paths[]`
  - `path`
  - `category`
  - `policy`
  - `reason`

建議 `category` 值：

- `overlay-project-local`
- `mutable-generated`
- `archive-history`
- `template-only`
- `environment-local`

### G. Split Required

- `split_required[]`
  - `path`
  - `current_role`
  - `required_action`
  - `recommended_target`
  - `blocker`
  - `done_when`

用途：記錄「目前不能直接 subtree 管」的 mutable hotspot。

### H. Skill Ownership

- `skill_ownership.selection_rule`
- `skill_ownership.builtin_core_packages[]`
- `skill_ownership.review_required_package_dirs[]`
- `skill_ownership.local_install_target`
- `skill_ownership.source_of_truth`
- `skill_ownership.notes`

用途：把 `.agent/skills/` 內哪些 builtin package 屬於 curated core、哪些目前仍屬 review-required，明確寫死，避免之後用 wildcard 把整棵 tree 一起帶進 subtree。

### I. Projection / Bootstrap Delivery

- `projection_bootstrap.delivery_model`
- `projection_bootstrap.artifact_path`
- `projection_bootstrap.invocation_owner`
- `projection_bootstrap.downstream_requirement`
- `projection_bootstrap.notes`

用途：固定 projection/bootstrap 的交付模型，避免 rollout 前一直停留在「需要 projection」但沒有決定 artifact 到底由誰交付。

### J. Shared Verification Strategy

- `verification_strategy.portable_smoke_suite_path`
- `verification_strategy.trigger_points[]`
- `verification_strategy.downstream_repo_tests_policy`
- `verification_strategy.notes`

用途：在 `tests/**` 不進 core 的前提下，仍保留一套可隨 core 一起交付的 portable smoke suite，作為 release / sync 的共用驗證入口。

### K. Automation Contract

- `automation_contract.canonical_manifest_path`
- `automation_contract.commands_must_read_manifest[]`
- `automation_contract.forbidden_fallback`
- `automation_contract.notes`

用途：明確規定 release/sync automation 的共同讀檔來源與禁止行為，避免 `precheck`、`apply`、`verify` 各自 hardcode 不同 prefix 規則。

---

## 4. 第一版 YAML 格式

下面這份就是建議直接採用的 `core_ownership_manifest.yml` 第一版格式。

第一版 machine-readable artifact 現已 materialize 到 repo root 的 `./core_ownership_manifest.yml`；下面的內容應與該檔保持一致。

```yaml
manifest_version: "1.0"
core_id: "agent-workflow-core"
baseline_repo: "foreverwow001/agent-workflow-template"
baseline_ref: "main"
generated_from: "2026-03-19 current repo analysis"

strategy:
  source_of_truth: "curated-exported-core"
  transport: "git-subtree"
  export_model: "export-branch-or-export-tree"
  downstream_default: "overlay-outside-managed-paths-only"

root_path_contract:
  required_live_paths:
    - ".agent/workflows/**"
    - ".agent/runtime/**"
    - ".agent/roles/**"
    - ".agent/skills/**"
    - ".agent/templates/**"
    - "doc/implementation_plan_index.md"
    - "doc/plans/**"
    - "doc/logs/**"
  required_live_prefixes:
    - ".agent/"
    - "doc/"
  delivery_mode: "preserve-root-live-paths"
  projection_strategy: "materialize-curated-core-at-root-or-project-via-bootstrap"
  projection_script: "required-if-exported-core-is-not-materialized-at-root"
  blocking_assumptions:
    - "AGENT_ENTRY.md opens ./.agent/workflows/dev-team.md and ./doc/implementation_plan_index.md directly"
    - "workflow and role docs call .agent/skills/** canonical paths directly"
  notes:
    - "current workflow documents and runtime assume root-level live paths like ./.agent/... and ./doc/..."
    - "subtree is transport only; do not change export prefix until root-path assumptions are explicitly redesigned or projected back"
    - "required_live_paths are runtime-required paths, not necessarily core-owned paths; doc/implementation_plan_index.md remains a downstream overlay artifact"

migration_constraints:
  primary_mutable_hotspot: ".agent/skills/**"
  do_not_optimize_first:
    - ".agent/workflows/**"
  primary_path_coupling: "AGENT_ENTRY.md and downstream workflow docs assume root .agent and doc live paths"
  subtree_role: "transport-mechanism-only"
  required_before_transport:
    - "split mutable skill metadata, local installs, and generated outputs out of subtree-managed core paths"
    - "preserve root live paths or provide an explicit projection/bootstrap script"

skill_ownership:
  selection_rule: "only curated builtin package dirs explicitly listed here are subtree-managed core; do not export .agent/skills/** by wildcard"
  builtin_core_packages:
    - ".agent/skills/code-reviewer/**"
    - ".agent/skills/doc-generator/**"
    - ".agent/skills/test-runner/**"
    - ".agent/skills/plan-validator/**"
    - ".agent/skills/git-stats-reporter/**"
    - ".agent/skills/skills-evaluator/**"
    - ".agent/skills/github-explorer/**"
    - ".agent/skills/skill-converter/**"
    - ".agent/skills/manifest-updater/**"
  review_required_package_dirs:
    - ".agent/skills/codex-collaboration-bridge/**"
    - ".agent/skills/deep-research/**"
    - ".agent/skills/explore-cli-tool/**"
    - ".agent/skills/fact-checker/**"
    - ".agent/skills/persistent-terminal/**"
    - ".agent/skills/project-planner/**"
    - ".agent/skills/python-expert/**"
    - ".agent/skills/refactor/**"
    - ".agent/skills/security-review-helper/**"
    - ".agent/skills/typescript-expert/**"
  local_install_target: ".agent/skills_local/**"
  source_of_truth: ".agent/skills/_shared/__init__.py:PACKAGED_SKILL_ENTRIES plus explicit curation review"
  notes:
    - "builtin skill ownership must be explicit because current .agent/skills tree mixes curated core packages with other package-like directories"
    - "review_required package dirs are not implicitly excluded forever, but they must not enter subtree-managed core until curated"

projection_bootstrap:
  delivery_model: "core-managed-bootstrap-artifact"
  artifact_path: ".agent/runtime/scripts/workflow_core_projection.py"
  invocation_owner: "workflow-core sync apply"
  downstream_requirement: "artifact ships with core; downstream should not need a separately preinstalled wrapper"
  notes:
    - "projection/bootstrap is a runtime delivery artifact, not a maintainer-only note"
    - "its job is to materialize or validate required live paths after subtree sync when direct-root delivery is not used"

verification_strategy:
  portable_smoke_suite_path: ".agent/runtime/scripts/portable_smoke/workflow_core_smoke.py"
  trigger_points:
    - "after workflow-core release precheck ownership checks"
    - "after workflow-core sync apply projection/bootstrap"
    - "whenever projection/bootstrap delivery changes"
    - "whenever a split_required item is claimed complete"
  downstream_repo_tests_policy: "downstream repos still own tests/**; core ships only a portable smoke suite"
  notes:
    - "shared verification must travel with core because tests/** remains excluded from subtree-managed export"
    - "portable smoke is the common contract check, not a replacement for downstream project tests"

automation_contract:
  canonical_manifest_path: "./core_ownership_manifest.yml"
  commands_must_read_manifest:
    - "workflow-core sync precheck"
    - "workflow-core sync apply"
    - "workflow-core sync verify"
    - "workflow-core release precheck"
  forbidden_fallback: "do not maintain separate hardcoded managed/overlay/state prefix lists per command once the manifest exists"
  notes:
    - "machine-readable ownership truth must live in one file so release and sync tooling cannot drift"

managed_paths:
  - path: "core_ownership_manifest.yml"
    kind: "file"
    ownership: "core"
    sync_policy: "subtree-managed"
    downstream_edit_policy: "upstream-only"
    reason: "canonical machine-readable source of truth for release/sync automation"

  - path: ".agent/workflows/**"
    kind: "glob"
    ownership: "core"
    sync_policy: "subtree-managed"
    downstream_edit_policy: "upstream-only"
    reason: "active workflow contract and operator entry surface"

  - path: ".agent/workflows/references/**"
    kind: "glob"
    ownership: "core"
    sync_policy: "subtree-managed"
    downstream_edit_policy: "upstream-only"
    reason: "role-level trigger checklists and workflow reference set"

  - path: ".agent/runtime/tools/vscode_terminal_pty/**"
    kind: "glob"
    ownership: "core"
    sync_policy: "subtree-managed"
    downstream_edit_policy: "upstream-only"
    reason: "primary workflow runtime"

  - path: ".agent/runtime/tools/vscode_terminal_fallback/**"
    kind: "glob"
    ownership: "core"
    sync_policy: "subtree-managed"
    downstream_edit_policy: "upstream-only"
    reason: "consented fallback runtime"

  - path: ".agent/runtime/scripts/**"
    kind: "glob"
    ownership: "core"
    sync_policy: "subtree-managed"
    downstream_edit_policy: "upstream-only"
    reason: "bootstrap, preflight, install, recovery automation"

  - path: ".agent/VScode_system/**"
    kind: "glob"
    ownership: "core"
    sync_policy: "subtree-managed"
    downstream_edit_policy: "upstream-only"
    reason: "coordinator and workspace operation contract"

  - path: ".agent/roles/coordinator.md"
    kind: "file"
    ownership: "core"
    sync_policy: "subtree-managed"
    downstream_edit_policy: "upstream-only"
    reason: "active coordinator role contract"

  - path: ".agent/roles/planner.md"
    kind: "file"
    ownership: "core"
    sync_policy: "subtree-managed"
    downstream_edit_policy: "upstream-only"
    reason: "active planner role contract"

  - path: ".agent/roles/engineer.md"
    kind: "file"
    ownership: "core"
    sync_policy: "subtree-managed"
    downstream_edit_policy: "upstream-only"
    reason: "active engineer role contract"

  - path: ".agent/roles/qa.md"
    kind: "file"
    ownership: "core"
    sync_policy: "subtree-managed"
    downstream_edit_policy: "upstream-only"
    reason: "active QA role contract"

  - path: ".agent/roles/security.md"
    kind: "file"
    ownership: "core"
    sync_policy: "subtree-managed"
    downstream_edit_policy: "upstream-only"
    reason: "active security review contract"

  - path: ".agent/skills/schemas/**"
    kind: "glob"
    ownership: "core"
    sync_policy: "subtree-managed"
    downstream_edit_policy: "upstream-only"
    reason: "public output schema set"

  - path: ".agent/skills/_shared/__init__.py"
    kind: "file"
    ownership: "core"
    sync_policy: "subtree-managed"
    downstream_edit_policy: "upstream-only"
    reason: "shared helpers and canonical path resolver code"

  - path: ".agent/skills/code-reviewer/**"
    kind: "glob"
    ownership: "core"
    sync_policy: "subtree-managed"
    downstream_edit_policy: "upstream-only"
    reason: "curated builtin core skill package"

  - path: ".agent/skills/doc-generator/**"
    kind: "glob"
    ownership: "core"
    sync_policy: "subtree-managed"
    downstream_edit_policy: "upstream-only"
    reason: "curated builtin core skill package"

  - path: ".agent/skills/test-runner/**"
    kind: "glob"
    ownership: "core"
    sync_policy: "subtree-managed"
    downstream_edit_policy: "upstream-only"
    reason: "curated builtin core skill package"

  - path: ".agent/skills/plan-validator/**"
    kind: "glob"
    ownership: "core"
    sync_policy: "subtree-managed"
    downstream_edit_policy: "upstream-only"
    reason: "curated builtin core skill package"

  - path: ".agent/skills/git-stats-reporter/**"
    kind: "glob"
    ownership: "core"
    sync_policy: "subtree-managed"
    downstream_edit_policy: "upstream-only"
    reason: "curated builtin core skill package"

  - path: ".agent/skills/skills-evaluator/**"
    kind: "glob"
    ownership: "core"
    sync_policy: "subtree-managed"
    downstream_edit_policy: "upstream-only"
    reason: "curated builtin core skill package"

  - path: ".agent/skills/github-explorer/**"
    kind: "glob"
    ownership: "core"
    sync_policy: "subtree-managed"
    downstream_edit_policy: "upstream-only"
    reason: "curated builtin core skill package"

  - path: ".agent/skills/skill-converter/**"
    kind: "glob"
    ownership: "core"
    sync_policy: "subtree-managed"
    downstream_edit_policy: "upstream-only"
    reason: "curated builtin core skill package"

  - path: ".agent/skills/manifest-updater/**"
    kind: "glob"
    ownership: "core"
    sync_policy: "subtree-managed"
    downstream_edit_policy: "upstream-only"
    reason: "curated builtin core skill package"

  - path: ".agent/templates/handoff_template.md"
    kind: "file"
    ownership: "core"
    sync_policy: "subtree-managed"
    downstream_edit_policy: "upstream-only"
    reason: "reusable workflow template artifact"

  - path: "doc/plans/Idx-000_plan.template.md"
    kind: "file"
    ownership: "core"
    sync_policy: "subtree-managed"
    downstream_edit_policy: "upstream-only"
    reason: "canonical plan template"

  - path: "doc/logs/Idx-000_log.template.md"
    kind: "file"
    ownership: "core"
    sync_policy: "subtree-managed"
    downstream_edit_policy: "upstream-only"
    reason: "canonical log template"

excluded_paths:
  - path: "project_rules.md"
    category: "overlay-project-local"
    policy: "never-export"
    reason: "downstream project rule source must stay project-specific"

  - path: ".agent/roles/domain_expert.md"
    category: "overlay-project-local"
    policy: "never-export"
    reason: "domain expert content is expected to vary by downstream project"

  - path: "doc/implementation_plan_index.md"
    category: "overlay-project-local"
    policy: "never-export"
    reason: "active index is project-local state, not portable core template truth"

  - path: "doc/plans/Idx-*_plan.md"
    category: "mutable-generated"
    policy: "never-export"
    reason: "active plans are per-project artifacts"

  - path: "doc/logs/Idx-*_log.md"
    category: "mutable-generated"
    policy: "never-export"
    reason: "active logs are per-project artifacts"

  - path: "maintainers/**"
    category: "archive-history"
    policy: "never-export"
    reason: "maintainer governance is template-repo-local history and analysis"

  - path: ".agent/workflow_baseline_rules.md"
    category: "template-only"
    policy: "never-export"
    reason: "template self-maintenance rule source, not downstream active rule source"

  - path: ".agent/PORTABLE_WORKFLOW.md"
    category: "template-only"
    policy: "never-export"
    reason: "transport/setup guidance, not subtree-managed runtime core"

  - path: ".agent/PR_PREPARATION.md"
    category: "template-only"
    policy: "never-export"
    reason: "repo-maintenance helper, not workflow runtime core"

  - path: ".agent/scripts/setup_workflow.sh"
    category: "template-only"
    policy: "never-export"
    reason: "bootstrap/setup helper should remain outside subtree-managed core"

  - path: ".agent/scripts/run_codex_template.sh"
    category: "template-only"
    policy: "never-export"
    reason: "template helper script, not portable managed core"

  - path: ".devcontainer/**"
    category: "environment-local"
    policy: "never-export"
    reason: "container shape is project- and maintainer-local"

  - path: "tests/**"
    category: "overlay-project-local"
    policy: "never-export"
    reason: "downstream repos should own their own test surface and adoption pace; shared portable smoke travels separately under .agent/runtime/scripts/**"

  - path: ".service/**"
    category: "mutable-generated"
    policy: "never-export"
    reason: "runtime capture and bridge state"

  - path: ".venv/**"
    category: "environment-local"
    policy: "never-export"
    reason: "local environment only"

  - path: "**/__pycache__/**"
    category: "mutable-generated"
    policy: "never-export"
    reason: "generated cache"

split_required:
  - path: ".agent/skills/_shared/skill_manifest.json"
    current_role: "runtime-written skill registry"
    required_action: "move out of subtree-managed core path"
    recommended_target: ".agent/state/skills/skill_manifest.json"
    blocker: "normal tool usage will dirty subtree"
    done_when: "shared helpers read/write overlay state path instead of core path"

  - path: ".agent/skills/_shared/skill_whitelist.json"
    current_role: "project-local approval policy"
    required_action: "move to project-local overlay config"
    recommended_target: ".agent/config/skills/skill_whitelist.json"
    blocker: "downstream approval policy should not be overwritten by subtree sync"
    done_when: "whitelist policy is no longer stored under subtree-managed core"

  - path: ".agent/skills/_shared/audit.log"
    current_role: "append-only runtime audit trail"
    required_action: "move to generated state location"
    recommended_target: ".agent/state/skills/audit.log"
    blocker: "every runtime action dirties subtree"
    done_when: "audit writes land outside managed core path"

  - path: ".agent/skills/INDEX.md"
    current_role: "mixed static catalog plus generated local entries"
    required_action: "split builtin core catalog from local/generated skill index"
    recommended_target: ".agent/skills/INDEX.md + .agent/state/skills/INDEX.local.md"
    blocker: "external skill installs currently rewrite a subtree-managed file"
    done_when: "core index is stable and local additions are written outside subtree"

  - path: ".agent/skills/<external-installed-packages>/**"
    current_role: "user-downloaded or locally-installed skills"
    required_action: "move external install destination out of core-managed skills tree"
    recommended_target: ".agent/skills_local/**"
    blocker: "downstream local installs currently collide with subtree-managed core packages"
    done_when: "builtin skills and local skills no longer share the same managed directory"
```

---

## 5. V1 使用規則

若採用這份 manifest，建議同時遵守以下操作規則：

1. `managed_paths` 內的路徑，預設只能 upstream 改，不能下游直接 patch。
2. `excluded_paths` 內的路徑，不得從 subtree export source 帶入。
3. `split_required` 內任一項未完成前，不要直接把目前 repo main 當成 subtree source。
4. `migration_constraints` 內的條件優先於任何 subtree transport 設計；不要先搬 `.agent/workflows/**`，卻把 `.agent/skills/**` 的 mutable state 留在 core tree。
5. 若 export source 不直接 materialize 到 root，必須先提供 projection/bootstrap script，保證 `AGENT_ENTRY.md` 與其下游 live path 仍成立。
6. 實際 subtree transport 應只針對「curated export source」，不是原 repo 所有 active 路徑。
7. `doc/implementation_plan_index.md` 雖是 required live path，但仍屬 downstream overlay artifact；core 只保證入口 contract，不應把 project-local index 直接收回 subtree-managed core。
8. projection/bootstrap 應以 core-managed runtime artifact 交付，不應依賴 downstream 事先安裝獨立 wrapper。
9. `workflow-core sync precheck|apply|verify` 與 `workflow-core release precheck` 應共讀 `./core_ownership_manifest.yml`，不得各自 hardcode 一套 prefix 規則。

---

## 6. 目前最重要的結論

第一版 manifest 已足夠回答三個關鍵問題：

1. 哪些路徑可以被 core 擁有
2. 哪些路徑一定不能進 subtree
3. 哪些 mutable hotspot 必須先拆

因此後續若要進入實作，下一個自然步驟不是直接 subtree，而是先完成 `split_required` 的拆分。

另外，真正開始實作前，還應同時確認四件事已定型：

1. `doc/implementation_plan_index.md` 已被視為 required live path 但非 core-owned artifact
2. curated builtin skill packages 與 review-required skill package dirs 已分開列明
3. projection/bootstrap 的 artifact path 與交付責任已固定
4. release/sync automation 將以 repo root `./core_ownership_manifest.yml` 作為共同 machine-readable source of truth
