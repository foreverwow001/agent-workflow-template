# -*- coding: utf-8 -*-
"""
.agent/skills/skill-converter/scripts/skill_converter.py
=====================================
用途：技能轉換流水線模組
職責：驗證下載批准、補齊中文 header、適配專案慣例，並更新技能索引
=====================================
"""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Tuple


SKILLS_DIR = Path(__file__).resolve().parents[2]
if str(SKILLS_DIR) not in sys.path:
    sys.path.insert(0, str(SKILLS_DIR))

from _shared import LOCAL_INDEX_PATH, LOCAL_SKILLS_DIR, skill_name_to_package_dir  # noqa: E402


HEADER_TEMPLATE = '''# -*- coding: utf-8 -*-
"""
{file_path}
=====================================
用途：{description}
來源：{source_repo}
下載日期：{download_date}
=====================================

⚠️ 此技能由 GitHub Explorer 自動下載並轉換
原始來源：https://github.com/{source_repo}
"""

'''


LOCAL_INDEX_TEMPLATE = '''# Local Skills Overlay Index

> 本檔追蹤安裝在 `.agent/skills_local/` 的 external/local skills。
> core builtin catalog 仍以 `.agent/skills/INDEX.md` 為準；這裡只記錄 overlay additions。

## 📦 Local Skills

| 技能名稱 | 用途 | 調用指令 |
|----------|------|----------|

---

## 🔍 技能詳細說明
'''


SKILL_MD_TEMPLATE = '''---
name: {skill_name}
description: "{description}"
---

# {title}

## 用途

{description}

## 來源

- GitHub: https://github.com/{source_repo}
- 下載日期：{download_date}

## Canonical 結構

- package doc: `{package_doc_path}`
- canonical file: `{canonical_file_path}`

## 使用方式

```bash
{usage}
```
'''


def validate_approval(user_confirmed: bool) -> Dict[str, Any]:
    if not user_confirmed:
        return {
            "status": "blocked",
            "approved": False,
            "message": "⛔ 安全機制：必須先執行 preview 並加上 --confirm 參數確認下載",
            "action_required": "請使用：python .agent/skills/github-explorer/scripts/github_explorer.py download <repo> <file> --confirm",
        }
    return {"status": "success", "approved": True, "message": "✅ 使用者已確認批准"}


def has_chinese_header(content: str) -> bool:
    return any(re.search(r"[\u4e00-\u9fff]", line) for line in content.splitlines()[:10])


def add_chinese_header(
    content: str,
    skill_name: str,
    source_repo: str,
    package_relative_path: str,
    package_root_relative: str,
    description: Optional[str] = None,
) -> Tuple[str, bool]:
    if has_chinese_header(content):
        return content, False

    resolved_description = description
    if not resolved_description:
        docstring_match = re.search(r'"""(.*?)"""', content, re.DOTALL)
        if docstring_match:
            first_line = docstring_match.group(1).strip().split("\n")[0]
            resolved_description = first_line[:50] if first_line else f"來自 {source_repo} 的技能"
        else:
            resolved_description = f"來自 {source_repo} 的技能"

    content = re.sub(r"^# -\*- coding: utf-8 -\*-\s*\n?", "", content)
    header = HEADER_TEMPLATE.format(
        file_path=f"{package_root_relative}/{package_relative_path}",
        description=resolved_description,
        source_repo=source_repo,
        download_date=datetime.now().strftime("%Y-%m-%d"),
    )
    return header + content, True


def build_usage_command(package_root_relative: str, package_relative_path: str, path: Path) -> Optional[str]:
    if path.suffix == ".py":
        return f"python {package_root_relative}/{package_relative_path}"
    return None


def ensure_local_index() -> None:
    if LOCAL_INDEX_PATH.exists():
        return
    LOCAL_INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    LOCAL_INDEX_PATH.write_text(LOCAL_INDEX_TEMPLATE, encoding="utf-8")


def resolve_package_root(skill_name: str, path: Path) -> Tuple[Path, str]:
    package_dir = skill_name_to_package_dir(skill_name)
    local_package_root = LOCAL_SKILLS_DIR / package_dir
    core_package_root = SKILLS_DIR / package_dir

    if path.is_relative_to(local_package_root) or (local_package_root.exists() and not path.is_relative_to(core_package_root)):
        return local_package_root, f".agent/skills_local/{package_dir}"
    if path.is_relative_to(core_package_root) or core_package_root.exists():
        return core_package_root, f".agent/skills/{package_dir}"

    inferred_root = path.parents[1] if path.parent.name == "scripts" else path.parent
    if inferred_root.is_relative_to(LOCAL_SKILLS_DIR):
        return inferred_root, f".agent/skills_local/{inferred_root.relative_to(LOCAL_SKILLS_DIR).as_posix()}"
    if inferred_root.is_relative_to(SKILLS_DIR):
        return inferred_root, f".agent/skills/{inferred_root.relative_to(SKILLS_DIR).as_posix()}"
    return inferred_root, str(inferred_root)


def adapt_to_project_convention(content: str) -> Tuple[str, list[str]]:
    changes: list[str] = []
    hardcoded_patterns = [
        (r"/home/\w+/", "/path/to/"),
        (r"C:\\\\Users\\\\[^\\\\]+\\\\", "C:\\\\Users\\\\user\\\\"),
        (r"C:/Users/[^/]+/", "C:/Users/user/"),
    ]
    for pattern, replacement in hardcoded_patterns:
        if re.search(pattern, content):
            content = re.sub(pattern, replacement, content)
            changes.append(f"移除 hardcoded 路徑模式: {pattern}")

    if "json.dumps" in content and "ensure_ascii" not in content:
        changes.append("⚠️ 建議：json.dumps 應加入 ensure_ascii=False 以支援中文")

    for pattern in [r"sk-[a-zA-Z0-9]{20,}", r'api[_-]?key\s*=\s*["\'][^"\']+["\']']:
        if re.search(pattern, content, re.IGNORECASE):
            changes.append("🚨 警告：偵測到可能的 API Key，請手動檢查")

    return content, changes


def update_init_py(skill_name: str) -> Dict[str, Any]:
    return {
        "status": "success",
        "message": f"ℹ️ __init__.py 改為動態掃描模式，技能 {skill_name} 無需手動加入 AVAILABLE_SKILLS",
    }


def update_skill_index(skill_name: str, description: str, usage: str, source_repo: str) -> Dict[str, Any]:
    try:
        ensure_local_index()
        content = LOCAL_INDEX_PATH.read_text(encoding="utf-8")
        table_row = f"| `{skill_name}` | {description} | `{usage}` |\n"
        table_row_pattern = re.compile(rf"^\| `{re.escape(skill_name)}` \|.*$", re.MULTILINE)
        if table_row_pattern.search(content):
            content = table_row_pattern.sub(table_row.rstrip("\n"), content, count=1)
        else:
            table_anchor = r"(\|----------\|------\|----------\|\n)"
            if re.search(table_anchor, content):
                content = re.sub(table_anchor, f"\\1{table_row}", content, count=1)
            else:
                content += "\n## 📦 Local Skills\n\n| 技能名稱 | 用途 | 調用指令 |\n|----------|------|----------|\n" + table_row

        detail_pattern = re.compile(
            rf"### (\d+)\. {re.escape(skill_name)} \(外部技能\)\n\n.*?(?=\n### \d+\. |\Z)",
            re.DOTALL,
        )
        existing_detail = detail_pattern.search(content)
        detail_index = existing_detail.group(1) if existing_detail else str(len(list(re.finditer(r"### \d+\.", content))) + 1)
        detail_section = f"""
### {detail_index}. {skill_name} (外部技能)

**功能**：{description}

**來源**：[{source_repo}](https://github.com/{source_repo})

**調用方式**：
```bash
{usage}
```

**下載日期**：{datetime.now().strftime("%Y-%m-%d")}

"""
        if existing_detail:
            content = detail_pattern.sub(detail_section.rstrip("\n"), content, count=1)
        else:
            content = content.rstrip() + "\n\n" + detail_section.lstrip("\n")

        LOCAL_INDEX_PATH.write_text(content.rstrip() + "\n", encoding="utf-8")
        return {"status": "success", "message": f"✅ 已將 {skill_name} 加入 INDEX.local.md"}
    except Exception as exc:
        return {"status": "error", "message": f"更新 INDEX.local.md 失敗：{exc}"}


def convert_skill(
    file_path: str,
    skill_name: str,
    source_repo: str,
    description: Optional[str] = None,
    package_relative_path: Optional[str] = None,
    user_confirmed: bool = False,
) -> Dict[str, Any]:
    approval = validate_approval(user_confirmed)
    if not approval.get("approved"):
        return approval

    path = Path(file_path)
    if not path.exists():
        return {"status": "error", "message": f"檔案不存在：{file_path}"}

    try:
        content = path.read_text(encoding="utf-8")
    except Exception as exc:
        return {"status": "error", "message": f"讀取檔案失敗：{exc}"}

    results: Dict[str, Any] = {
        "status": "success",
        "skill_name": skill_name,
        "source_repo": source_repo,
        "steps": [],
    }
    package_root, package_root_relative = resolve_package_root(skill_name, path)
    if package_relative_path:
        relative_path = Path(package_relative_path)
    else:
        try:
            relative_path = path.relative_to(package_root)
        except ValueError:
            relative_path = Path(path.name)

    if relative_path.is_absolute() or ".." in relative_path.parts:
        return {"status": "error", "message": f"不支援的 package 相對路徑：{relative_path}"}

    if path.suffix == ".py":
        content, header_added = add_chinese_header(
            content,
            skill_name,
            source_repo,
            relative_path.as_posix(),
            package_root_relative,
            description,
        )
        results["steps"].append("✅ 已加入繁體中文 Header" if header_added else "ℹ️ 已有中文 Header，跳過")
        content, changes = adapt_to_project_convention(content)
        results["steps"].extend(changes)
        path.write_text(content, encoding="utf-8")
        results["steps"].append(f"✅ 已更新 {path.name}")

        skill_doc = package_root / "SKILL.md"
        if not skill_doc.exists():
            skill_doc.write_text(
                SKILL_MD_TEMPLATE.format(
                    skill_name=skill_name,
                    description=description or f"來自 {source_repo} 的外部技能",
                    title=skill_name.replace("_", " ").title(),
                    source_repo=source_repo,
                    download_date=datetime.now().strftime("%Y-%m-%d"),
                    package_doc_path=f"{package_root_relative}/SKILL.md",
                    canonical_file_path=f"{package_root_relative}/{relative_path.as_posix()}",
                    usage=build_usage_command(package_root_relative, relative_path.as_posix(), path),
                ),
                encoding="utf-8",
            )
            results["steps"].append("✅ 已建立外部技能 SKILL.md")

    init_result = update_init_py(skill_name)
    results["steps"].append(init_result.get("message", "更新 __init__.py"))

    usage = build_usage_command(package_root_relative, relative_path.as_posix(), path)
    if usage:
        index_result = update_skill_index(skill_name, description or f"來自 {source_repo} 的技能", usage, source_repo)
        results["steps"].append(index_result.get("message", "更新 INDEX.local.md"))
    else:
        results["steps"].append("ℹ️ 非可執行檔案，跳過 INDEX.local.md 更新")
    results["message"] = f"✅ 技能 {skill_name} 轉換完成"
    return results


def main(argv: list[str] | None = None) -> int:
    result = {
        "status": "info",
        "message": "此模組由 github_explorer.py 內部調用",
        "available_functions": [
            "validate_approval",
            "add_chinese_header",
            "adapt_to_project_convention",
            "update_init_py",
            "update_skill_index",
            "convert_skill",
        ],
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


__all__ = [
    "validate_approval",
    "has_chinese_header",
    "add_chinese_header",
    "build_usage_command",
    "adapt_to_project_convention",
    "update_init_py",
    "update_skill_index",
    "convert_skill",
    "main",
]


if __name__ == "__main__":
    raise SystemExit(main())
