# Coordinator Research Skill Trigger Checklist

這是 Coordinator 在 Research Gate 中判定是否載入 `deep-research` / `fact-checker` 的唯一表格來源。

## 使用規則

- 逐列檢查
- 任一列命中即載入對應 skill
- 若同時命中多列，必須全部載入
- 若未命中任何列，不必因 Research Gate 額外載入這兩個 skill

## Trigger Checklist

| Checklist Item | 如何判定 | 必載 Skill |
|---|---|---|
| `research_required: true` | Plan 的 `RESEARCH & ASSUMPTIONS` 明確標記 | `deep-research` |
| 依賴檔案變更 | 變更命中 `requirements.txt`、`pyproject.toml`、`*requirements*.txt` | `deep-research` |
| 需求明確要求研究/比較 | Goal / SPEC / user request 含 `research`、`investigate`、`compare`、`evaluate`、`trade-off`、`migration`、`version compatibility`、`official docs`、`upstream behavior` | `deep-research` |
| Plan 需要 repo 外可驗證事實 | 不靠 repo 內文檔就無法成立的外部技術 / 版本 / 官方能力判斷 | `deep-research` |
| 版本或棄用聲明 | 最低版本、支援矩陣、發布 / 移除 / 棄用時點 | `fact-checker` |
| API capability / limitation 聲明 | 支援與否、限制、required configuration、feature flag、provider capability | `fact-checker` |
| 數值聲明 | 配額、限制、timeout、latency、benchmark、size limit、throughput | `fact-checker` |
| 安全 / 政策 / 法遵聲明 | 官方保證、CVE、permission / auth / compliance、policy requirement | `fact-checker` |
| 平台 / runtime 相容性聲明 | 作業系統、runtime、provider support matrix、environment compatibility | `fact-checker` |

## 對應載入命令

### deep-research

```bash
cat .agent/skills/deep-research/SKILL.md
cat .agent/skills/deep-research/references/research-process.md
cat .agent/skills/deep-research/references/source-policy-and-output.md
```

### fact-checker

```bash
cat .agent/skills/fact-checker/SKILL.md
cat .agent/skills/fact-checker/references/verification-process.md
cat .agent/skills/fact-checker/references/verdict-and-context.md
```
