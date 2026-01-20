# Changelog v1.2.0 (Idx-019)

**Release Date**: 2026-01-20

## 🔄 Summary

本次更新將 dev-team workflow 同步至 Ivyhousetw-META 最新版本，並移除已廢棄的 SendText Bridge 自動化機制。

## ❌ Removed

- **SendText Bridge Extension** (`tools/sendtext-bridge/`)
  - 包含 3 個 vsix 版本 (0.0.1, 0.0.2, 0.0.3)
  - extension.js, package.json 等檔案
- **SendText Bridge Scripts**
  - `.agent/scripts/sendtext.sh` - CLI wrapper
  - `.agent/scripts/auto_execute_plan.sh` - 自動執行腳本
- **SendText Bridge Documentation**
  - `tools/SENDTEXT_BRIDGE_GUIDE.md`

**移除理由**: SendText Bridge 為實驗性質的 VS Code extension，現已由 VS Code 內建的 `terminal.sendText` API + Proposed API 取代，功能更穩定且不需額外安裝。

## ➕ Added

- **VS Code System Config** (`.agent/VScode_system/`)
  - `Ivy_Coordinator.md` - Copilot Chat 協調器設定
  - `chat_instructions_ivy_house_rules.md` - Chat 指令與規則
  - `prompt_dev.md` - /dev 指令定義
  - `tool_sets.md` - 工具集設定

## 🔄 Changed

- **Workflow Documentation** - 同步至 Ivyhousetw-META (commit `5373f03`)
  - `.agent/workflows/dev-team.md` - 更新為最新 7-stage workflow
  - `.agent/workflows/AGENT_ENTRY.md` - 同步入口規範
- **README.md** - 移除 SendText Bridge 功能說明，改為 VS Code 原生整合
- **setup_workflow.sh** - 註解掉 SendText Bridge 複製步驟（保留註解供參考）

## 🔙 Migration Guide

### 從 v1.1.0 升級

1. **移除舊版 SendText Bridge**（若已安裝）:
   ```bash
   # 移除 VS Code extension（若已安裝）
   code --uninstall-extension sendtext-bridge-*.vsix
   
   # 刪除本地檔案
   rm -rf tools/sendtext-bridge
   rm .agent/scripts/sendtext.sh .agent/scripts/auto_execute_plan.sh
   ```

2. **使用新的執行方式**:
   - Coordinator（GitHub Copilot Chat）使用 `terminal.sendText()` 對 Codex/OpenCode 終端注入指令
   - 監測使用 VS Code Proposed API（`terminalDataWriteEvent`）
   - 詳見 `.agent/workflows/dev-team.md` Step 2.5, Step 3

### 需要 Legacy 版本？

若仍需使用 SendText Bridge，請查閱：
- **Tag**: `v1.1.0-sendtext-legacy`（建議建立此 tag 指向 commit `a1e456a`）
- **Branch**: `archive/sendtext-bridge`（可選，建立備份 branch）

## 📚 References

- **Source Repository**: [Ivyhousetw-META](https://github.com/foreverwow001/Ivyhousetw-META)
- **Idx-019 Plan**: `.agent/plans/Idx-019_sync_template_with_ivyhousetw-META_plan.md`
- **Commit**: `e84279b` (workflow sync), `5907098` (remove sendtext)

---

**Maintainer**: @foreverjojo  
**Related Issue**: Idx-019
