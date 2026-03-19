---
name: fact-checker
description: "Coordinator claim verification skill. Use when a plan, research note, user statement, version claim, API capability, numeric assertion, policy statement, or security claim must be checked before it can be treated as fact in workflow decisions."
---

# Fact Checker

提供 Coordinator 對單一或少量具體 claim 做證據導向驗證，避免把未核實的說法直接寫進 Plan、研究摘要或 workflow 決策。

## 何時使用

當任務符合任一條件時，Coordinator 應載入本 skill：

- Plan、research note 或 user 訊息中出現具體 factual claim
- 需要驗證版本號、API 能力、限制、數值、相容性或安全聲明
- 你懷疑某個敘述可能只是印象、傳聞或過時資訊

## Deterministic Trigger

Coordinator 若命中任一 claim 類型，必須載入本 skill：

- 版本相容性、最低版本、發布/移除/棄用時點
- API capability、支援與否、限制、required configuration
- 數值聲明：配額、限制、timeout、latency、benchmark、size limit、throughput
- 安全、政策、法遵、官方保證、CVE、permission / auth / compliance 聲明
- 平台、作業系統、runtime、provider support matrix 或 environment compatibility 聲明

## 核心要求

- 先抽出「可驗證 claim」，再驗證，不要對整段話一起下結論
- 明確區分 fact、opinion、interpretation
- 結論必須標示可信度與限制
- 若證據不足，應標註 unverifiable / unconfirmed，而不是硬判 true

## Coordinator 工作流

1. 先讀 [references/verification-process.md](./references/verification-process.md) 確認驗證步驟。
2. 再讀 [references/verdict-and-context.md](./references/verdict-and-context.md) 統一 verdict 與上下文寫法。
3. 驗證後把結果回填到 Plan、research note 或 gate decision，不要讓未核實說法繼續漂浮在流程裡。
4. 若同時存在多個子議題需要系統性整理，先用 `deep-research`，再對關鍵 claim 疊加本 skill。

## 參考資料

- [references/verification-process.md](./references/verification-process.md)
- [references/verdict-and-context.md](./references/verdict-and-context.md)
