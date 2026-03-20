# Chat Session 維護規範

> 這份規範用於維護 `agent-workflow-template` 時的 Chat 交接，不是下游專案模板內容。

## 目標

- 保留足夠的上下文，讓公司與家裡兩台電腦能順利接續工作
- 避免把原始 chat export 直接提交到公開 template repo
- 把真正需要長期保存的內容濃縮成可讀的 handoff 摘要

## 文件索引

### Authoritative

- `2026-03-19-terminal-tooling-source-map.md`
  - terminal tooling 現行規則來源的 maintainer 導航入口；active truth 已移到 runtime README 與 preflight script
- `handoff/core-overlay/`
  - 集中放置 core + overlay / subtree sync 的 maintainer handoff 文件；請先看 `handoff/core-overlay/README.md`，其下目前包含 `daily-sync-sop.md`、`sync-checklist.md` 與 `cli-spec.md`
- `handoff/SESSION-HANDOFF.template.md`
  - 可重複使用的 handoff 模板

> 注意：active 區只保留目前仍承擔規則來源或導航角色的文件；若 active truth 已明確轉移到 runtime README / script，舊 maintainer 文檔應降級為 archive 歷史，而不是繼續佔住 active surface。

### Active Supporting Docs

- `2026-03-19-core-ownership-manifest-v1.md`
  - subtree/core-overlay 方案下的第一版 core ownership manifest 欄位與 current-repo baseline
- `2026-03-19-subtree-mutable-path-split-checklist.md`
  - subtree sync 前必做的 mutable path 拆分清單與完成判定

> MT-003 `/dev` workflow 文件收斂工作已正式結案；其現況流程、friction 地圖、rotation patch 提案與關帳快照，現已存入 `maintainers/archive/2026-03-18-workflow-optimization-plan.md`，active chat 區不再保留對應 supporting doc。

### History

- `archive/`
  - 放已完成的狀態摘要、過渡期 checklist、舊分析與已失效 handoff
  - 這些文件保留設計脈絡，但不再作為現行規則來源
- `../archive/2026-03-19-maintainers-folder-migration-checklist.md`
  - `maintainers/` 搬遷已完成後的正式 migration record；GitHub template 內容僅作歷史與交付決策分析，不是現行推薦路徑
- `archive/2026-03-13-terminal-pty-target-architecture-and-migration-principles.md`
  - 舊的 terminal tooling 架構基準；active 入口已由 `2026-03-19-terminal-tooling-source-map.md` 取代
- `archive/2026-03-13-pty-monitor-and-capture-contract.md`
  - 舊的 PTY monitor / capture 契約；active 入口已回收進 PTY README
- `archive/2026-03-13-merged-fallback-tool-spec.md`
  - 舊的 fallback spec；active 入口已回收進 fallback README
- `archive/2026-03-13-preflight-migration-plan.md`
  - 舊的 preflight migration 設計文；active 入口已回收進 preflight script
- `archive/2026-03-19-terminal-tooling-archive-checklist.md`
  - 本次 retire `2026-03-13` active set 前使用的短 checklist
- `archive/README.md`
  - archive 收錄條件、draft/handoff 收斂規則與刪除門檻

> 非 chat 類的 maintainer 歷史文件，請改放 `maintainers/archive/`，不要混進 `chat/archive/`。

## 2026-03-19 清理結果

- `2026-03-13` terminal-tooling active set 已整批降級為 archive；active maintainer 入口改由 `2026-03-19-terminal-tooling-source-map.md` 承接。
- PTY / fallback / preflight 的現行 truth 不再由 dated chat docs 直接承擔，而是回到 runtime README 與 script 本體。
- 本次 archive 前 checklist 已完成並一併移入 `archive/`，不保留在 active 區。

## 2026-03-17 清理結果

- Active docs 維持不合併：目前 `architecture principles`、`monitor/capture contract`、`fallback spec`、`preflight migration plan` 各自承擔不同治理層級，沒有再收斂的必要。
- 已完成的 dated handoff 全數降級為歷史文檔並移入 `archive/`；`handoff/` 只保留「目前仍需接手的交接摘要」與模板。
- Archive 已做一次實質收斂：原本三份 fallback draft 已改由單一摘要檔 `archive/2026-03-13-merged-fallback-tool-draft-lineage.md` 取代。
- `2026-03-17-dev-workflow-current-flow-and-optimization-map.md` 已先併入 `maintainers/archive/2026-03-18-workflow-optimization-plan.md`，原檔保留為 archive 歷史快照。
- Archive 中仍保留的文件以「歷史脈絡」為主，不再承擔 active 規則來源角色。
- Archive 準則已獨立成 `archive/README.md`，後續 handoff / draft 收斂應以該檔為準。

## 先講清楚的限制

- 目前不要假設 GitHub Copilot Chat 會把同一段本機 chat session 原生同步到另一台電腦。
- VS Code Settings Sync 可同步編輯器偏好，但不等於跨機續聊同一段 chat。
- 因此跨公司 / 家裡切換時，應以 `Chat: Export Chat...` + handoff 摘要作為正式交接方式。

## 目錄規則

- `maintainers/chat/*.json`
  - 放原始 `Chat: Export Chat...` 的 JSON
  - 這些檔案應留在本機或 OneDrive
  - 已由 `.gitignore` 排除，不應提交
- `maintainers/chat/handoff/**/*.md`
  - 只放目前仍需接手的交接摘要與 active handoff/SOP/spec
  - 單次 session handoff 應直接放在 `handoff/` 根目錄
  - 只有長期維護的一組 SOP / checklist / spec 才應集中在單一子資料夾，例如 `handoff/core-overlay/`
  - 任務或里程碑一旦完成，應移入 `archive/`
  - 目前 active handoff 除模板外，也保留 `handoff/core-overlay/` 這組仍在演進中的 subtree/core-overlay 文件；但 dated session handoff 應放回 `handoff/` 根目錄；MT-003 關帳快照已移入 archive
- `maintainers/chat/archive/*.md`
  - 放已完成或已被取代的 maintainer 文檔
  - 不應再被當成 authoritative 規則來源
- `maintainers/chat/archive/README.md`
  - 放 archive 治理規則
  - 規定哪些 handoff / draft 保留、合併、移除

## 建議工作流程

1. 工作做到一半要換電腦前，先執行 `Chat: Export Chat...`
2. 把 JSON 存到 `maintainers/chat/`
3. 依 [handoff/SESSION-HANDOFF.template.md](handoff/SESSION-HANDOFF.template.md) 寫一份摘要
4. 只提交 handoff 摘要，不提交原始 JSON
5. 在另一台電腦開工時，先讀 handoff，再視需要打開本機或 OneDrive 上的原始 JSON

若該 handoff 對應的工作已完成，請在收尾時把它移到 `archive/`，避免 `handoff/` 長期堆積已失效交接。

> 若你只想快速照表操作，請直接看 `doc/HOME_OFFICE_SWITCH_SOP.md`。

## 命名建議

### 原始 JSON

- `2026-03-10-devcontainer-dual-mode-01.json`
- `2026-03-10-template-doc-refresh-01.json`

### handoff 摘要

- `2026-03-10-devcontainer-dual-mode.md`
- `2026-03-10-template-doc-refresh.md`
