# Verdict And Context

## 建議 Verdict

- `SUPPORTED`：有足夠可信來源支持
- `PARTIALLY_SUPPORTED`：大方向正確，但缺 context 或部分條件不同
- `CONFLICTING_EVIDENCE`：來源彼此衝突，無法直接定論
- `UNVERIFIED`：目前沒有足夠可驗證來源
- `INCORRECT`：已有可信來源反駁

## 每次輸出至少包含

- Claim
- Verdict
- Confidence
- Key evidence
- Important caveat / context

## 回填原則

- 若 verdict 不是 `SUPPORTED`，不要把原 claim 當既定事實寫進 Plan
- 若 claim 影響技術選型、版本選擇或風險判斷，應把 caveat 一併寫回 Plan
