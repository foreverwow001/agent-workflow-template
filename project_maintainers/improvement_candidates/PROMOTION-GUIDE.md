# Promotion Guide

這份文件定義 downstream / 新專案在發現改進做法後，如何判斷它應留在 project-local，還是應 promotion 回 workflow template repo。

## 1. Promotion criteria

符合以下條件越多，越適合 promotion 回 upstream：

- 問題不是單一專案特例，而是 workflow / skill / runtime 的共通 friction
- 解法不依賴特定產品邏輯、專案政策、或私有整合
- 同一類型的新專案高機率也會再次遇到
- 已有明確 evidence，證明修正後流程更穩定、更清楚、或更不易踩坑
- 能明確指出應更新的 target，例如 skill、runtime script、workflow doc、SOP

若只滿足少數條件，先留在 project-local，等更多驗證後再判斷。

## 2. What should go upstream

以下內容通常適合回 upstream：

- workflow contract 的通用修正
- runtime / bootstrap / preflight 的通用硬化
- skills 中可攜、可重用的操作方法或判斷規則
- maintainer SOP / portable workflow 中與單一專案無關的更佳做法
- 能降低多個 downstream 專案重複踩坑機率的修正

## 3. What should stay project-local

以下內容通常應留在 project-local：

- 專案特有 policy
- 專案私有整合或部署限制
- 特定技術棧、服務商、內部流程才成立的 workaround
- 僅對單一 repo 結構或單一團隊作業模式有效的做法
- 尚未確認是否可跨專案重用的觀察

## 4. Decision rules

判斷順序建議如下：

1. 先問：這是不是只因某個專案的產品邏輯、政策或環境而成立？
   - 若是，留在 project-local。
2. 再問：下一個新專案大機率也會遇到相同 friction 嗎？
   - 若否，先留在 project-local。
3. 再問：這個改法是否能對應到明確的 upstream target？
   - 若不能，先補清楚 candidate，再不要急著 promotion。
4. 再問：是否已有足夠 evidence 支持它不是一次性的 workaround？
   - 若沒有，先維持 candidate 狀態。
5. 若以上答案大多偏向可重用，再建立 upstream follow-up，人工 promotion 回 workflow template repo。

## 5. Recommended flow

1. 在 project-local 開發中先記錄 handoff、plan、log 與 local fix。
2. 若懷疑某個做法可重用，再整理成 improvement candidate。
3. 經人工 review 後，決定：
   - 留在 project-local
   - 等更多案例驗證
   - promotion 回 upstream
4. 只有 promotion 回 upstream 並被正式吸收後，它才應被視為未來 agents / skills / docs 可依賴的 reusable knowledge。
