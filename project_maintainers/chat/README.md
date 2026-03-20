# Project Chat Handoff Guide

這個目錄提供 downstream / 新專案自己的 chat handoff 落點。

用途：

- 讓同一個專案能跨機器、跨 session、跨人接續工作
- 保存可提交的 handoff 摘要，而不是把原始 chat export 直接當成權威文件

目錄建議：

- `handoff/`：目前仍需要接手的交接摘要與 handoff template
- `archive/`：已完成或已失效的 handoff 歷史

注意：

- `maintainers/` 是 template repo 自己的 maintainer surface，不應直接拿來當 downstream 專案的 active handoff 區
- 這裡也不是 authoritative workflow 規則來源；它屬於 supporting operational memory
- upstream 目前只交付 skeleton files；你在新專案後續新增的 dated handoff / archive 文件應由該專案自己維護
