# Agent Workflow Template Baseline Rules

> 此檔僅用於維護 `agent-workflow-template` 這個 template repo 本身。
> 新專案落地時，active rule source 應改為 repo 根目錄的 `project_rules.md`；本檔不應取代下游專案規則。

---

## 1. 溝通與互動契約

- 所有回覆、Plan、Log、維護文檔與說明一律使用繁體中文。
- 進入實作前，必須先完成 `READ_BACK_REPORT`，並優先使用 VS Code `#askQuestions` 完成 user-facing Gate。
- `READ_BACK_REPORT` 確認後，先決定 `formal-workflow` 或 `lightweight-direct-edit`；若 scope 擴張或命中風險條件，必須升級回正式 workflow。

## 2. Workflow 契約

- active artifact path 一律使用 `doc/implementation_plan_index.md`、`doc/plans/Idx-NNN_plan.md`、`doc/logs/Idx-NNN_log.md`。
- Gate、`EXECUTION_BLOCK` 欄位契約、Security Review trigger 的唯一來源是 `.agent/workflows/AGENT_ENTRY.md`。
- GitHub Copilot Chat 固定為 Coordinator，不納入正式 `/dev` workflow 的 Engineer / Security Reviewer / QA 工具選單。
- Engineer / Security Reviewer / QA 工具只允許 `codex-cli` 或 `copilot-cli`。
- workflow 主路徑固定使用 `.agent/runtime/tools/vscode_terminal_pty`；fallback 只在 PTY 不可用且 user 明確同意後啟用。

## 3. Template Repo 維護限制

- 維護 template repo 時，不得把根目錄 `project_rules.md` 視為 active authoritative 規則檔；它保留為下游專案 starter template。
- `.agent/plans/**`、`.agent/logs/**` 僅視為歷史 artifact，不是 active workflow 的預設輸出路徑。
- 變更 workflow 契約時，需同步檢查 authoritative 與 supporting docs，避免多重真相來源。
- 禁止對 Codex CLI / Copilot CLI terminal 注入 git 指令；git 只可在 Project terminal 或 VS Code SCM 執行。

## 4. 安全與敏感資料

- 不得 hard-code API key、token、secret、password 或其他敏感憑證。
- 敏感資料必須透過環境變數或安全設定來源載入。
- 若任務命中 `auth`、`security`、`api`、`bridge`、`subprocess`、`upload`、`template`、`token`、`secret`、`session`、`oauth`、`jwt` 等高風險面，必須依 `AGENT_ENTRY.md` 的 deterministic 規則進入 Security Review。
