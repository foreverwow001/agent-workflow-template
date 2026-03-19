# Python Type Safety

## Type Safety

- 函式簽名與回傳值提供 type hints
- 複雜資料容器優先使用 dataclass / typed object，而不是散落 dict
- 泛型場景可使用 `TypeVar` / parameterized collections
- 對跨模組 public API 優先補齊型別，再做結構抽象

## 自檢

- [ ] 函式有型別與回傳型別
- [ ] 核心資料結構沒有過度依賴裸 dict
- [ ] 泛型與 optional 邊界有清楚表達
