# Source Policy And Output

## 來源政策

- 優先使用 user 提供的官方連結
- 允許使用 repo 內文檔與現有程式碼作為第一手上下文
- 若使用者未提供外部來源，且 workflow 明確要求 link-required，則不得把未驗證外部印象包裝成 `Sources`
- 無法驗證時，改寫進 `Assumptions` 並標註 `RISK: unverified`

## 建議輸出落點

將研究結果回填到 Plan：

- `## 🔍 RESEARCH & ASSUMPTIONS`
- `### Sources`
- `### Assumptions`
- 必要時在 `## ⚠️ 注意事項` 補上 research-derived 風險

## 不要做的事

- 不要把研究輸出寫成與 Plan 平行的第二份規格
- 不要在來源不夠時給出過度自信的結論
- 不要把未經驗證的數字、版本、效能聲明直接當事實
