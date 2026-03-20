# Template Maintainers Index

> 此索引只用於維護 `agent-workflow-template` 本身，不用於未來使用此 template 的專案開發任務。

## 📋 維護任務索引

| Task ID | 名稱 | 狀態 | 建立日期 | 完成日期 | 說明 |
|---------|------|------|---------|---------|------|
| MT-001 | Dev Container 雙軌模式整理 | In Progress | 2026-03-10 | - | Dockerfile 主模式 + GHCR 加速模式 |
| MT-002 | Terminal PTY 架構收斂 | In Progress | 2026-03-13 | - | PTY 主路徑 + merged fallback tool 目標架構定版 |
| MT-003 | Workflow 文件收斂優化 | Completed | 2026-03-15 | 2026-03-18 | 已完成 path/Gate 收斂、baseline split、Mode Selection Gate、PTY rotation 與互動 smoke 驗證 |
| MT-004 | Copilot CLI 全域遷移 | Completed | 2026-03-16 | 2026-03-17 | active runtime 與命名面全面切換到 Copilot CLI |

## 📚 維護文件

- [devcontainer_modes.md](devcontainer_modes.md) - 雙軌 Dev Container 模式與切換方式
- [archive/2026-03-18-workflow-optimization-plan.md](archive/2026-03-18-workflow-optimization-plan.md) - MT-003 `/dev` workflow 文件收斂的關帳紀錄與歷史計畫快照
- [archive/2026-03-19-maintainers-folder-migration-checklist.md](archive/2026-03-19-maintainers-folder-migration-checklist.md) - `maintainers/` 搬遷完成後的正式 migration record
- [chat/README.md](chat/README.md) - Chat 匯出與交接摘要規範
- [chat/2026-03-19-terminal-tooling-source-map.md](chat/2026-03-19-terminal-tooling-source-map.md) - terminal tooling 現行規則來源的 maintainer 導航入口
- [chat/handoff/SESSION-HANDOFF.template.md](chat/handoff/SESSION-HANDOFF.template.md) - 交接摘要模板
- [chat/archive/](chat/archive/) - 已完成的狀態摘要、draft 與舊 handoff 歷史存檔
- [chat/archive/README.md](chat/archive/README.md) - archive 收錄條件、合併準則與刪除門檻
- [release_artifacts/README.md](release_artifacts/README.md) - 正式 workflow-core release note / metadata 的固定存放位置
- [chat/archive/2026-03-13-terminal-pty-target-architecture-and-migration-principles.md](chat/archive/2026-03-13-terminal-pty-target-architecture-and-migration-principles.md) - 已退役的 terminal tooling 架構基準歷史檔
- [chat/archive/2026-03-13-pty-monitor-and-capture-contract.md](chat/archive/2026-03-13-pty-monitor-and-capture-contract.md) - 已退役的 PTY monitor / capture 契約歷史檔
- [chat/archive/2026-03-13-merged-fallback-tool-spec.md](chat/archive/2026-03-13-merged-fallback-tool-spec.md) - 已退役的 merged fallback spec 歷史檔
- [chat/archive/2026-03-13-preflight-migration-plan.md](chat/archive/2026-03-13-preflight-migration-plan.md) - 已退役的 preflight migration 歷史檔
- [chat/archive/2026-03-19-terminal-tooling-archive-checklist.md](chat/archive/2026-03-19-terminal-tooling-archive-checklist.md) - retire `2026-03-13` active set 前使用的短 checklist
- [chat/archive/2026-03-13-merged-fallback-tool-draft-lineage.md](chat/archive/2026-03-13-merged-fallback-tool-draft-lineage.md) - 已刪 fallback draft 的合併摘要與替代說明
- [chat/archive/2026-03-17-dev-workflow-current-flow-and-optimization-map.md](chat/archive/2026-03-17-dev-workflow-current-flow-and-optimization-map.md) - 已合併進 `archive/2026-03-18-workflow-optimization-plan.md` 的 `/dev` 歷史分析快照
- [chat/archive/2026-03-18-workflow-optimization-handoff.md](chat/archive/2026-03-18-workflow-optimization-handoff.md) - MT-003 正式關帳 handoff 歷史快照
- [archive/README.md](archive/README.md) - 非 chat 類 maintainer 歷史文件的 archive 邊界說明
- [archive/2026-03-16-copilot-cli-migration-checklist.md](archive/2026-03-16-copilot-cli-migration-checklist.md) - 已完成的 Copilot CLI 遷移清單與驗證證據（歷史紀錄）
- [archive/2026-03-18-workflow-optimization-plan.md](archive/2026-03-18-workflow-optimization-plan.md) - MT-003 `/dev` workflow 文件收斂的完整 closure record
- [../doc/NEW_MACHINE_SETUP.md](../doc/NEW_MACHINE_SETUP.md) - 新機開工流程
- [../doc/ENVIRONMENT_RECOVERY.md](../doc/ENVIRONMENT_RECOVERY.md) - 環境故障排查與回復流程
- [../doc/HOME_OFFICE_SWITCH_SOP.md](../doc/HOME_OFFICE_SWITCH_SOP.md) - 公司與家裡切換一頁版 SOP

## 🔁 切機重點

- VS Code Settings Sync 用來同步偏好，不用來假設可原生續聊同一段 Copilot Chat。
- Chat 跨機接續以 export JSON + handoff 摘要為準。

## 🔒 邊界說明

- [../doc/implementation_plan_index.md](../doc/implementation_plan_index.md) 是 template 使用者建立自己專案後的任務索引模板。
- 本資料夾記錄的是 template 維護者自己的環境、文件與結構演進，不應混入下游專案計畫。

---

**最後更新**: 2026-03-18
