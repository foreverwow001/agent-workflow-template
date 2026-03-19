# Refactor Python

## 優先修法

- 將大函式拆成小型 pure helper + orchestration function
- 將鬆散 dict 轉為 dataclass 或明確 typed structure
- 以具體例外與邊界驗證取代隱性失敗路徑
- 把重複資料轉換邏輯抽為 utility / service function
- 以 named constant 取代魔法數字與狀態字串

## Python 注意事項

- 重構時不要順手把錯誤處理策略改成不同 exception contract
- 若從 dict 改 dataclass，先確認對外 API / serialization 是否保持一致
- 使用 comprehension 或 helper 抽象時，仍要維持可讀性，不要為了「更 Pythonic」讓意圖更隱晦
