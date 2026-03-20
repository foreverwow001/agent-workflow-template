# Terminal Tooling Active Source Map

> 建立日期：2026-03-19
> 狀態：Active
> 用途：接手 `2026-03-13` terminal-tooling active set 的 maintainer 導航角色，明確指出目前 terminal tooling 的現行規則來源在哪裡。

> 這份文件本身不是新的 workflow 規格；它只定義「現在應去哪裡讀 active truth」。真正的行為基準仍在 runtime README 與 preflight script。

## 現行來源

| 主題 | Active source | 說明 |
|---|---|---|
| PTY 主路徑定位、artifact contract、stable event、recovery / fallback handoff | `.agent/runtime/tools/vscode_terminal_pty/README.md` | 取代舊的 PTY architecture + monitor/capture active 入口 |
| fallback scope、bridge、legacy verify/capture 邊界 | `.agent/runtime/tools/vscode_terminal_fallback/README.md` | 取代舊的 merged fallback active spec 入口 |
| preflight aggregate model、PTY layer / fallback layer readiness | `.agent/runtime/scripts/vscode/workflow_preflight_check.py`、`.agent/runtime/scripts/vscode/workflow_preflight_fallback.py` | 取代舊的 preflight migration active 入口 |

## 2026-03-19 archive 決議

下列 4 份文件自 2026-03-19 起轉為歷史文檔，保留設計脈絡，但不再承擔 active 規則來源角色：

- `maintainers/chat/archive/2026-03-13-terminal-pty-target-architecture-and-migration-principles.md`
- `maintainers/chat/archive/2026-03-13-pty-monitor-and-capture-contract.md`
- `maintainers/chat/archive/2026-03-13-merged-fallback-tool-spec.md`
- `maintainers/chat/archive/2026-03-13-preflight-migration-plan.md`

## 讀取順序

1. 先讀這份 source map，確認你要追的是哪一層 active truth。
2. 要看 PTY 主路徑契約時，直接讀 `.agent/runtime/tools/vscode_terminal_pty/README.md`。
3. 要看 fallback 邊界時，直接讀 `.agent/runtime/tools/vscode_terminal_fallback/README.md`。
4. 要看 preflight readiness 實際語意時，直接讀對應的 preflight script。
5. 只有在需要追歷史決策脈絡時，才回頭讀 archive 裡的 `2026-03-13` 文件。
