# -*- coding: utf-8 -*-
"""
.agent/skills/__init__.py
=====================================
用途：Skills 根模組初始化與公開 package 索引
職責：提供動態 AVAILABLE_SKILLS、shared metadata 路徑與 canonical package 可見性
=====================================
"""

from __future__ import annotations

from ._shared import (
    CONFIG_SKILLS_DIR,
    CANONICAL_MANIFEST_PATH,
    CANONICAL_WHITELIST_PATH,
    INDEX_PATH,
    LEGACY_MANIFEST_PATH,
    LEGACY_WHITELIST_PATH,
    LOCAL_INDEX_PATH,
    LOCAL_SKILLS_DIR,
    PACKAGED_SKILL_ENTRIES,
    PUBLIC_SCHEMAS_DIR,
    SHARED_DIR,
    SKILLS_DIR,
    STATE_SKILLS_DIR,
    iter_local_skill_package_dirs,
    iter_skill_package_dirs,
    package_dir_to_skill_name,
)


def _scan_available_skills() -> list[str]:
    discovered = {package_dir_to_skill_name(path.name) for path in iter_skill_package_dirs()}
    discovered.update(package_dir_to_skill_name(path.name) for path in iter_local_skill_package_dirs())
    return sorted(discovered)


AVAILABLE_SKILLS = _scan_available_skills()
BUILTIN_PACKAGED_SKILLS = sorted(PACKAGED_SKILL_ENTRIES)
SHARED_METADATA_PATHS = {
    "shared_dir": str(SHARED_DIR),
    "state_dir": str(STATE_SKILLS_DIR),
    "config_dir": str(CONFIG_SKILLS_DIR),
    "local_skills_dir": str(LOCAL_SKILLS_DIR),
    "canonical_manifest": str(CANONICAL_MANIFEST_PATH),
    "canonical_whitelist": str(CANONICAL_WHITELIST_PATH),
    "legacy_manifest": str(LEGACY_MANIFEST_PATH),
    "legacy_whitelist": str(LEGACY_WHITELIST_PATH),
    "schemas_dir": str(PUBLIC_SCHEMAS_DIR),
    "index": str(INDEX_PATH),
    "local_index": str(LOCAL_INDEX_PATH),
}


__all__ = [
    "SKILLS_DIR",
    "SHARED_DIR",
    "PUBLIC_SCHEMAS_DIR",
    "INDEX_PATH",
    "AVAILABLE_SKILLS",
    "BUILTIN_PACKAGED_SKILLS",
    "SHARED_METADATA_PATHS",
]
