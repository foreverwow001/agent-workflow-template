# Python Performance

## Performance

- 簡單轉換或篩選優先用 comprehension
- 大資料流優先考慮 generator
- 使用 `with` 管理檔案、lock、連線等資源
- 先 profile 或有明確證據，再做進一步微優化

## 自檢

- [ ] 使用 context manager 管理資源
- [ ] 沒有明顯低效的重複計算或不必要 materialization
- [ ] 優化是基於證據，而不是猜測
