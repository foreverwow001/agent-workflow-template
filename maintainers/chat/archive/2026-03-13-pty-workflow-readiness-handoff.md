# SESSION-HANDOFF

> 建立日期：2026-03-13
> 狀態：Archived - milestone handoff

## Current goal

補記這一輪的三個結論：1. workflow / governance / operator 文件已正式收斂到 PTY-primary + consented-fallback 心智模型；2. PTY recovery 的 fallback handoff 已在 repo 內落成真實接手路徑，不再只是記錄 accepted；3. `proposed_api_true` / client allowlist 不再是後續主線，因為 fallback-ready 已接受 shell integration + bridge + token + artifact compatibility。

## Current branch

main

## Active container mode

- Standard Dockerfile mode
- Debian GNU/Linux 12 dev container

## Files touched

- .agent/workflows/AGENT_ENTRY.md
- .agent/workflows/dev-team.md
- .agent/roles/coordinator.md
- maintainers/chat/2026-03-13-preflight-migration-plan.md
- maintainers/chat/2026-03-13-merged-fallback-tool-spec.md
- maintainers/chat/2026-03-13-pty-monitor-and-capture-contract.md
- .agent/runtime/tools/vscode_terminal_pty/extension.js
- .agent/runtime/tools/vscode_terminal_fallback/extension.js
- .agent/runtime/scripts/vscode/workflow_preflight_check.py
- maintainers/chat/archive/2026-03-13-pty-workflow-readiness-handoff.md

## What has been confirmed

- workflow / governance / operator 文件主敘事已改成 `.agent/runtime/tools/vscode_terminal_pty` 是唯一 workflow 主路徑；fallback 只在 PTY 不可用且 user 明確同意後才接手。
- `workflow_preflight_check.py --require-pty --allow-pty-cold-start --json` 與 `workflow_preflight_check.py --require-fallback --json` 於本輪重新執行後都回 `status=pass`。
- PTY primary readiness 目前有實際 runtime evidence：`codex_pty_debug.jsonl` 與 `opencode_pty_debug.jsonl` 都存在，兩個 backend 在最近紀錄中都可看到 `pty.startup.ready` 與 `pty.command.succeeded`；兩邊也都有多輪 `pty.smoke.iteration.succeeded` / `pty.command.succeeded(command="smokeTest")`。
- workflow 文件層面，`dev-team.md` 與 `coordinator.md` 都已把主要命令面收斂成 `ivyhouseTerminalPty.start* / send* / submit* / verify*`，並把 fallback 改成條件式次路徑。
- PTY recovery flow 在 repo 程式碼中已不再把 fallback 視為單純 accepted 狀態；`.agent/runtime/tools/vscode_terminal_pty/extension.js` 會在 user 同意後真正嘗試啟動 fallback terminal / bridge，並對安全可重放的最後一步 `send` / `submit` 交由 fallback runtime 接手。
- fallback-ready 的 operator 判定已正式放寬為：Proposed API 不再是唯一門檻；只要 shell integration attachment、bridge healthz、token 與 artifact compatibility 成立，就可視為 ready。
- `proposed_api_true` / client allowlist 線索在本輪正式收尾：既然兩條 preflight 與 fallback runtime 都已可正常工作，後續不再把 allowlist 恢復成 true 視為必要工作。
- active 文件中的 index 路徑殘留已修正：`AGENT_ENTRY.md`、`planner.md`、`qa.md`、`PORTABLE_WORKFLOW.md` 現在都統一指向 repo 內จริง實存在的 `doc/implementation_plan_index.md`。
- 已完成一次嚴格照 `AGENT_ENTRY.md` 入口規則的文件化 dry-run：必讀檔路徑可成立，READ_BACK_REPORT gate 不再卡在不存在的 index 檔名，且 PTY-primary preflight 仍維持 `status=pass`。

## What was rejected

- 不再把 `proposed_api_true=false` 視為目前必修問題；它不再單獨阻擋 fallback-ready，也不是這輪 workflow readiness 的主要風險。
- 不把目前狀態描述成「整個 workflow 已 fully green end-to-end」；雖然入口文件卡點已排除，這一輪仍只做了文件化 dry-run 與 preflight 驗證，還沒有實際跑一次完整 slash-command workflow。
- 不再把 bridge-centric preflight 當成主判讀面；整體 workflow readiness 應先看 PTY layer，再看 fallback 是否可接手。

## Next exact prompt

請先讀這份 handoff。接下來不要再追 allowlist 或 Proposed API，也不要再回頭修 index 路徑殘留。這部分已完成。下一步若要再往前推，請直接做一次真正的 `/dev` workflow smoke：照 `AGENT_ENTRY.md` 輸出 READ_BACK_REPORT，確認 Approve Gate / Role Selection Gate / PTY-primary preflight / EXECUTION_BLOCK 回填描述是否能串成完整操作流程；若過程中還有文件與實際行為不一致，再把差異收斂進 active workflow docs，而不是只留在 handoff。

## Risks

- 目前主要風險已從「錯誤 index 路徑」轉成「文件化 dry-run 與真實 slash-command 執行之間是否仍有差距」；這一輪尚未實際跑完整 `/dev` workflow。
- workflow / 治理任務與專案功能任務現在都共用 `doc/implementation_plan_index.md`；若未來真的需要分出獨立 workflow index，必須在文件、模板與腳本中一起正式引入，不能再靠不存在的舊檔名佔位。

## Verification status

- 已驗證：`python .agent/runtime/scripts/vscode/workflow_preflight_check.py --require-pty --allow-pty-cold-start --json` 再次回 `status=pass`，且 `pty.backends.codex.status=ready`、`pty.backends.opencode.status=ready`。
- 已驗證：`python .agent/runtime/scripts/vscode/workflow_preflight_check.py --require-fallback --json` 回 `status=pass`；`shell_integration_attached.ok=true`、`sendtext_bridge_healthz.ok=true`、`sendtext_bridge_token.ok=true`、`artifact_compatibility.ok=true`，即使 `proposed_api_true.ok=false` 仍可通過。
- 已驗證：`codex_pty_debug.jsonl` 與 `opencode_pty_debug.jsonl` 中都存在近期 `pty.command.succeeded(command="smokeTest")` 與多輪 `pty.smoke.iteration.succeeded` evidence。
- 已驗證：workflow 文件中的 PTY-primary policy 已存在於 `AGENT_ENTRY.md`、`dev-team.md`、`coordinator.md`。
- 已驗證：重新依 `AGENT_ENTRY.md` 讀入口文件後，必讀清單與 READ_BACK_REPORT 模板現在都可指向存在的 index 檔，不再卡在 `Workflow_Plan_index.md` / `Implementation_Plan_index.md` 的舊檔名。
- 尚未驗證：這一輪尚未實際跑一次完整 slash-command `/dev` workflow，因此還不能把結果升格成真實互動層面的 end-to-end 綠燈。
