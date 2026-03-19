# Python Correctness

## Correctness 優先

- 避免 mutable default arguments
- 對 edge cases、boundary conditions、empty input 明確處理
- 例外處理要具體，不可 bare `except:` 後直接吞掉
- 需要失敗訊號時，回傳值與 exception 策略要一致

## 自檢

- [ ] 沒有 mutable default arguments
- [ ] 沒有 bare `except:`
- [ ] 邊界條件已覆蓋
- [ ] 主要錯誤路徑有一致處理策略
