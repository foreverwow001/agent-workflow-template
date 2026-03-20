# -*- coding: utf-8 -*-
"""
.agent/skills/_shared/__init__.py
=====================================
用途：Skills toolchain/shared metadata 路徑與存取輔助模組
職責：集中管理 canonical/shared metadata 路徑、package metadata 與 package-only 掃描輔助
=====================================
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, Iterable


SKILLS_DIR = Path(__file__).resolve().parents[1]
AGENT_DIR = SKILLS_DIR.parent
SHARED_DIR = Path(__file__).resolve().parent
PUBLIC_SCHEMAS_DIR = SKILLS_DIR / "schemas"
STATE_SKILLS_DIR = AGENT_DIR / "state" / "skills"
CONFIG_SKILLS_DIR = AGENT_DIR / "config" / "skills"
LOCAL_SKILLS_DIR = AGENT_DIR / "skills_local"

LEGACY_MANIFEST_PATH = SHARED_DIR / "skill_manifest.json"
LEGACY_WHITELIST_PATH = SHARED_DIR / "skill_whitelist.json"
LEGACY_AUDIT_LOG_PATH = SHARED_DIR / "audit.log"

CANONICAL_MANIFEST_PATH = STATE_SKILLS_DIR / "skill_manifest.json"
CANONICAL_WHITELIST_PATH = CONFIG_SKILLS_DIR / "skill_whitelist.json"
AUDIT_LOG_PATH = STATE_SKILLS_DIR / "audit.log"
INDEX_PATH = SKILLS_DIR / "INDEX.md"
LOCAL_INDEX_PATH = STATE_SKILLS_DIR / "INDEX.local.md"

NON_PACKAGE_DIRS = {"_shared", "schemas", "__pycache__"}

PACKAGED_SKILL_ENTRIES = {
    "code_reviewer": {
        "package_dir": "code-reviewer",
        "entry_doc": "SKILL.md",
        "script_rel": "scripts/code_reviewer.py",
    },
    "doc_generator": {
        "package_dir": "doc-generator",
        "entry_doc": "SKILL.md",
        "script_rel": "scripts/doc_generator.py",
    },
    "test_runner": {
        "package_dir": "test-runner",
        "entry_doc": "SKILL.md",
        "script_rel": "scripts/test_runner.py",
    },
    "plan_validator": {
        "package_dir": "plan-validator",
        "entry_doc": "SKILL.md",
        "script_rel": "scripts/plan_validator.py",
    },
    "git_stats_reporter": {
        "package_dir": "git-stats-reporter",
        "entry_doc": "SKILL.md",
        "script_rel": "scripts/git_stats_reporter.py",
    },
    "skills_evaluator": {
        "package_dir": "skills-evaluator",
        "entry_doc": "SKILL.md",
        "script_rel": "scripts/skills_evaluator.py",
    },
    "github_explorer": {
        "package_dir": "github-explorer",
        "entry_doc": "SKILL.md",
        "script_rel": "scripts/github_explorer.py",
    },
    "skill_converter": {
        "package_dir": "skill-converter",
        "entry_doc": "README.md",
        "script_rel": "scripts/skill_converter.py",
    },
    "manifest_updater": {
        "package_dir": "manifest-updater",
        "entry_doc": "SKILL.md",
        "script_rel": "scripts/manifest_updater.py",
    },
}


def read_json_file(path: Path, default: Dict[str, Any]) -> Dict[str, Any]:
    if not path.exists():
        return dict(default)
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return dict(default)


def read_json_file_with_legacy_fallback(path: Path, legacy_path: Path, default: Dict[str, Any]) -> Dict[str, Any]:
    if path.exists():
        return read_json_file(path, default)
    return read_json_file(legacy_path, default)


def write_json_file(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def read_manifest() -> Dict[str, Any]:
    default = {"version": "1.0", "skills": []}
    return read_json_file_with_legacy_fallback(CANONICAL_MANIFEST_PATH, LEGACY_MANIFEST_PATH, default)


def write_manifest(payload: Dict[str, Any]) -> None:
    write_json_file(CANONICAL_MANIFEST_PATH, payload)


def read_whitelist() -> Dict[str, Any]:
    default = {
        "version": "1.0",
        "approved_sources": [],
        "approval_policy": {
            "auto_approve_official_orgs": False,
            "require_manual_approval_for_personal_repos": True,
            "minimum_stars": 0,
            "maximum_repo_age_months": 0,
        },
    }
    return read_json_file_with_legacy_fallback(CANONICAL_WHITELIST_PATH, LEGACY_WHITELIST_PATH, default)


def write_whitelist(payload: Dict[str, Any]) -> None:
    write_json_file(CANONICAL_WHITELIST_PATH, payload)


def skill_name_to_package_dir(skill_name: str) -> str:
    value = re.sub(r"[^a-z0-9]+", "-", skill_name.strip().lower().replace("_", "-"))
    value = re.sub(r"-+", "-", value).strip("-")
    return value or "external-skill"


def package_dir_to_skill_name(package_dir_name: str) -> str:
    value = re.sub(r"[^a-z0-9]+", "_", package_dir_name.strip().lower().replace("-", "_"))
    value = re.sub(r"_+", "_", value).strip("_")
    return value or "external_skill"


def is_skill_package_dir(path: Path) -> bool:
    if not path.is_dir():
        return False
    if path.name in NON_PACKAGE_DIRS:
        return False
    return (path / "SKILL.md").exists() or (path / "README.md").exists()


def iter_skill_package_dirs(root_dir: Path | None = None) -> Iterable[Path]:
    base_dir = root_dir or SKILLS_DIR
    if not base_dir.exists():
        return
    for child in sorted(base_dir.iterdir()):
        if is_skill_package_dir(child):
            yield child


def iter_local_skill_package_dirs() -> Iterable[Path]:
    yield from iter_skill_package_dirs(LOCAL_SKILLS_DIR)


def get_schema_file(skill_name: str) -> Path | None:
    schema_file = PUBLIC_SCHEMAS_DIR / f"{skill_name}_output.schema.json"
    return schema_file if schema_file.exists() else None


def get_public_schema_path(skill_name: str) -> str | None:
    schema_file = get_schema_file(skill_name)
    if schema_file is None:
        return None
    return f".agent/skills/schemas/{schema_file.name}"


def get_package_metadata(skill_name: str) -> Dict[str, str] | None:
    meta = PACKAGED_SKILL_ENTRIES.get(skill_name)
    if not meta:
        return None
    package_dir = meta["package_dir"]
    entry_doc = meta["entry_doc"]
    script_rel = meta["script_rel"]
    return {
        "path": f".agent/skills/{package_dir}/{script_rel}",
        "package_path": f".agent/skills/{package_dir}/{entry_doc}",
        "script_path": f".agent/skills/{package_dir}/{script_rel}",
    }


__all__ = [
    "SKILLS_DIR",
    "AGENT_DIR",
    "SHARED_DIR",
    "PUBLIC_SCHEMAS_DIR",
    "STATE_SKILLS_DIR",
    "CONFIG_SKILLS_DIR",
    "LOCAL_SKILLS_DIR",
    "CANONICAL_MANIFEST_PATH",
    "CANONICAL_WHITELIST_PATH",
    "AUDIT_LOG_PATH",
    "LEGACY_MANIFEST_PATH",
    "LEGACY_WHITELIST_PATH",
    "LEGACY_AUDIT_LOG_PATH",
    "INDEX_PATH",
    "LOCAL_INDEX_PATH",
    "NON_PACKAGE_DIRS",
    "PACKAGED_SKILL_ENTRIES",
    "read_json_file",
    "read_json_file_with_legacy_fallback",
    "write_json_file",
    "read_manifest",
    "write_manifest",
    "read_whitelist",
    "write_whitelist",
    "skill_name_to_package_dir",
    "package_dir_to_skill_name",
    "is_skill_package_dir",
    "iter_skill_package_dirs",
    "iter_local_skill_package_dirs",
    "get_schema_file",
    "get_public_schema_path",
    "get_package_metadata",
]
