# Improvement Candidates

這個目錄用來保存 downstream / 新專案在實作過程中發現的「候選改進經驗」。

它的定位不是已驗證的跨專案真相來源，而是待整理、待驗證、待 promotion 的候選區。

適合放進這裡的內容：

- 在新專案中遇到、並已找到較好解法的 workflow friction
- 可能值得回 upstream 的 skill / doc / runtime / SOP 改進點
- 需要多個專案再驗證一次，才能決定是否升格的做法

不適合直接放進這裡的內容：

- 單純的 session handoff：改放 `project_maintainers/chat/handoff/`
- 已完成、只剩歷史價值的交接：改放 `project_maintainers/chat/archive/`
- 已確認只屬於本專案的 policy、整合、限制：留在 project-local docs，不必 promotion

建議命名：

- dated candidate：`2026-03-20-pty-bootstrap-followup.md`
- 每份 candidate 應說明它是 project-local observation 還是疑似 reusable pattern

upstream 目前只交付 skeleton files；新專案後續新增的 dated candidate 文件屬於 downstream local overlay，不會自動回流到 workflow template repo。
