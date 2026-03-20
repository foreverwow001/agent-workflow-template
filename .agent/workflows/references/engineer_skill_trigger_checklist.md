# Engineer Skill Trigger Checklist

這是 Engineer 在實作前判定是否載入 `refactor`、`typescript-expert`、`python-expert` 的唯一表格來源。

## 使用規則

- 逐列檢查
- 任一列命中即載入對應 skill
- 若同時命中多列，必須全部載入
- 這份表只處理「實作前的工程技能載入」，不取代 QA / Security / Research Gate

## Trigger Checklist

| Checklist Item | 如何判定 | 必載 Skill |
|---|---|---|
| refactor 任務 | User / Planner / Plan 明確要求 refactor、cleanup、重整結構，或主要工作是 behavior-preserving restructuring | `refactor` |
| TypeScript / JavaScript 檔案變更 | 新增或修改 `.ts`、`.tsx`、`.js`、`.jsx` | `typescript-expert` |
| Python 檔案變更 | 新增或修改 `.py` | `python-expert` |
| React / Node 實作 | 任務明確涉及 React component、hook、Node service、API handler、前端狀態邏輯 | `typescript-expert` |
| Python correctness / typing / documentation 強化 | 任務明確涉及 type hints、docstring、錯誤處理、Pythonic 重構 | `python-expert` |

## 對應載入命令

### refactor

```bash
cat .agent/skills/refactor/SKILL.md
cat .agent/skills/refactor/references/refactor-workflow.md
cat .agent/skills/refactor/references/refactor-smells.md
```

### typescript-expert

```bash
cat .agent/skills/typescript-expert/SKILL.md
cat .agent/skills/typescript-expert/references/typescript-javascript-core.md
cat .agent/skills/typescript-expert/references/typescript-react-patterns.md
cat .agent/skills/typescript-expert/references/typescript-api-and-testing.md
```

### python-expert

```bash
cat .agent/skills/python-expert/SKILL.md
cat .agent/skills/python-expert/references/python-correctness.md
cat .agent/skills/python-expert/references/python-type-safety.md
cat .agent/skills/python-expert/references/python-performance.md
cat .agent/skills/python-expert/references/python-style-and-documentation.md
```
