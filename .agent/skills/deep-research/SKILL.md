---
name: deep-research
description: "Coordinator research synthesis skill. Use when research_required is true, when dependency or version changes need source-backed analysis, when a task needs multi-source synthesis before planning or execution, or when the user explicitly asks for investigation with citations."
---

# Deep Research

提供 Coordinator 在 Research Gate 或 SPEC_MODE 中做結構化研究整理，但輸出必須服從本 repo 的 source policy 與 plan workflow，而不是生成獨立長篇報告後脫離流程。

## 何時使用

當任務符合任一條件時，Coordinator 應載入本 skill：

- Plan 的 `research_required: true`
- 需求涉及外部技術、版本差異、官方能力、遷移方案或依賴選型
- User 明確要求 research / investigate / 比較多個方案
- 需要將多個官方來源或 repo 內文檔整理成可回填 Plan 的研究結論

## Deterministic Trigger

Coordinator 若命中任一條件，必須載入本 skill：

- `research_required: true`
- 依賴檔案變更（`requirements.txt`、`pyproject.toml`、`*requirements*.txt`）
- Goal / SPEC / 研究摘要含 `research`、`investigate`、`compare`、`evaluate`、`trade-off`、`migration`、`version compatibility`、`official docs`、`upstream behavior`
- Plan 需要 repo 外可驗證事實才能成立

## 核心要求

- 研究輸出是為了補齊 Plan 的 `RESEARCH & ASSUMPTIONS`，不是取代 Plan
- 優先整合 user 提供官方來源與 repo 內文檔
- 若沒有足夠可驗證來源，必須降級為 assumption 並標註 `RISK: unverified`
- 明確區分 consensus、uncertainty、trade-off，不要把研究摘要寫成結論先行的宣告

## Coordinator 工作流

1. 先讀 [references/research-process.md](./references/research-process.md) 確認研究順序。
2. 再讀 [references/source-policy-and-output.md](./references/source-policy-and-output.md) 確認允許來源與輸出格式。
3. 將研究結果濃縮回 Plan 的 `Sources` / `Assumptions` / risk note，而不是另外維護第二套 spec。
4. 若研究中出現具體 claim、版本數字、API 能力或安全聲明需要核實，再疊加 `fact-checker`。

## 參考資料

- [references/research-process.md](./references/research-process.md)
- [references/source-policy-and-output.md](./references/source-policy-and-output.md)
