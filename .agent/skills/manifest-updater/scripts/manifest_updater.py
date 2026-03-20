# -*- coding: utf-8 -*-
"""
.agent/skills/manifest-updater/scripts/manifest_updater.py
=====================================
用途：Skills Manifest 自動同步工具
職責：掃描 canonical package scripts，補齊 package metadata，並更新 canonical/shared manifest
=====================================
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple


SKILLS_DIR = Path(__file__).resolve().parents[2]
if str(SKILLS_DIR) not in sys.path:
    sys.path.insert(0, str(SKILLS_DIR))

from _shared import (  # noqa: E402
    CANONICAL_MANIFEST_PATH,
    PACKAGED_SKILL_ENTRIES,
    get_package_metadata,
    get_public_schema_path,
    read_manifest,
    write_manifest,
)


EXTERNAL_MARKERS = ("source_repo", "sha256_hash", "downloaded_at", "file_path", "commit_sha")


def validate_output_schema(result: Dict[str, Any], skill_name: str) -> Dict[str, Any]:
    """可選 JSON Schema 驗證（graceful degradation）"""
    try:
        import jsonschema
    except ImportError:
        return result

    schema_path = SKILLS_DIR / "schemas" / f"{skill_name}_output.schema.json"
    if not schema_path.exists():
        return result

    try:
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        jsonschema.validate(result, schema)
        return result
    except jsonschema.ValidationError as exc:
        result["validation_errors"] = [
            {"message": exc.message, "path": list(exc.path), "schema_path": list(exc.schema_path)}
        ]
        result.setdefault(
            "suggestion",
            f"輸出格式不符合 schema 規範。請檢查 {skill_name}_output.schema.json 並確認欄位正確性。",
        )
        return result
    except Exception:
        return result


def is_external_record(record: Dict[str, Any]) -> bool:
    if record.get("type") == "external":
        return True
    return any(key in record for key in EXTERNAL_MARKERS)


def is_builtin_record(record: Dict[str, Any]) -> bool:
    if record.get("type") == "builtin":
        return True
    path = record.get("path")
    if isinstance(path, str) and path.startswith(".agent/skills/") and not is_external_record(record):
        return True
    return False


def should_preserve_record(record: Dict[str, Any]) -> bool:
    return not is_builtin_record(record)


def read_first_purpose_line(py_file: Path) -> str:
    try:
        head = py_file.read_text(encoding="utf-8").splitlines()[:40]
    except Exception:
        return "（無法讀取用途）"
    for line in head:
        stripped = line.strip()
        if stripped.startswith("用途："):
            return stripped.replace("用途：", "").strip() or "（未提供用途）"
    return "（未提供用途）"


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def scan_builtin_skills(exclude_names: Iterable[str]) -> List[Dict[str, Any]]:
    exclude = set(exclude_names)
    skills: List[Dict[str, Any]] = []
    for skill_name in sorted(PACKAGED_SKILL_ENTRIES):
        if skill_name in exclude:
            continue
        packaged_entry = PACKAGED_SKILL_ENTRIES[skill_name]
        script_file = SKILLS_DIR / packaged_entry["package_dir"] / packaged_entry["script_rel"]
        if not script_file.exists():
            continue

        description_source = script_file
        package_meta = get_package_metadata(skill_name)
        if package_meta is None:
            continue
        record: Dict[str, Any] = {
            "name": skill_name,
            "type": "builtin",
            "version": "1.0.0",
            "path": package_meta["path"],
            "schema": get_public_schema_path(skill_name),
            "last_updated": _now_iso(),
        }
        record.update(package_meta)
        record["description"] = read_first_purpose_line(description_source)
        skills.append(record)
    return skills


def build_manifest(existing: Dict[str, Any]) -> Tuple[Dict[str, Any], int, int, int]:
    existing_skills = existing.get("skills", [])
    if not isinstance(existing_skills, list):
        existing_skills = []

    preserved = [entry for entry in existing_skills if isinstance(entry, dict) and entry.get("name") and should_preserve_record(entry)]
    external_names = [entry.get("name") for entry in preserved if isinstance(entry, dict) and entry.get("name") and is_external_record(entry)]
    builtin_skills = scan_builtin_skills(external_names)

    builtin_names = {entry["name"] for entry in builtin_skills}
    preserved_filtered = [entry for entry in preserved if entry.get("name") not in builtin_names]
    manifest = {
        "version": existing.get("version", "1.0"),
        "last_updated": _now_iso(),
        "skills": builtin_skills + preserved_filtered,
    }
    return manifest, len(builtin_skills), len(preserved_filtered), len(manifest["skills"])


def main(argv: List[str] | None = None) -> int:
    args = argv or sys.argv
    if "--sync" not in args and "--check" not in args:
        result = {
            "status": "error",
            "manifest_path": str(CANONICAL_MANIFEST_PATH),
            "message": "缺少參數（--sync 或 --check）",
            "usage": "python .agent/skills/manifest-updater/scripts/manifest_updater.py [--sync|--check]",
            "suggestion": "請使用 --check（不寫入）或 --sync（寫入更新）。",
        }
        print(json.dumps(validate_output_schema(result, "manifest_updater"), ensure_ascii=False, indent=2))
        return 2

    dry_run = "--check" in args and "--sync" not in args
    try:
        existing = read_manifest()
        new_manifest, builtin_count, preserved_count, total_count = build_manifest(existing)
    except Exception as exc:
        result = {
            "status": "error",
            "manifest_path": str(CANONICAL_MANIFEST_PATH),
            "message": f"更新 manifest 失敗：{exc}",
            "usage": "python .agent/skills/manifest-updater/scripts/manifest_updater.py [--sync|--check]",
            "suggestion": "請確認 skill_manifest.json 格式正確，且 .agent/skills 目錄可讀取。",
        }
        print(json.dumps(validate_output_schema(result, "manifest_updater"), ensure_ascii=False, indent=2))
        return 2

    if not dry_run:
        try:
            write_manifest(new_manifest)
        except Exception as exc:
            result = {
                "status": "error",
                "manifest_path": str(CANONICAL_MANIFEST_PATH),
                "message": f"寫入 manifest 失敗：{exc}",
                "suggestion": "請確認檔案權限可寫入，或改用 --check 先檢視更新結果。",
            }
            print(json.dumps(validate_output_schema(result, "manifest_updater"), ensure_ascii=False, indent=2))
            return 2

    result = {
        "status": "pass",
        "manifest_path": str(CANONICAL_MANIFEST_PATH),
        "dry_run": dry_run,
        "builtin_count": builtin_count,
        "preserved_count": preserved_count,
        "total_count": total_count,
        "summary": "已同步 builtin skills（含 canonical package metadata）並更新 canonical manifest" if not dry_run else "Dry run：已計算 manifest 更新結果",
    }
    print(json.dumps(validate_output_schema(result, "manifest_updater"), ensure_ascii=False, indent=2))
    return 0


__all__ = [
    "validate_output_schema",
    "is_external_record",
    "is_builtin_record",
    "should_preserve_record",
    "read_first_purpose_line",
    "scan_builtin_skills",
    "build_manifest",
    "main",
]


if __name__ == "__main__":
    raise SystemExit(main())
