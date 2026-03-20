---
name: manifest-updater
description: "Use when syncing builtin skill metadata, updating the canonical shared manifest, or validating the current skill catalog structure."
---

# Manifest Updater

## 用途

同步 skills manifest 的 builtin 清單，並更新 canonical shared manifest。

## Canonical 結構

- canonical script: `.agent/skills/manifest-updater/scripts/manifest_updater.py`

## 使用方式

```bash
python .agent/skills/manifest-updater/scripts/manifest_updater.py --check
python .agent/skills/manifest-updater/scripts/manifest_updater.py --sync
```
