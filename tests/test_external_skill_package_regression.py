# -*- coding: utf-8 -*-
"""
tests/test_external_skill_package_regression.py
=====================================
用途：驗證 external skill download/converter/rollback 的 package-only regression 行為
職責：
  - 驗證 resolver 會把 nested scripts/resources 歸到同一個 skill package
  - 驗證 download + converter 會保留 remote 相對路徑
  - 驗證 rollback 會同步清除 package、manifest 與 INDEX 條目
=====================================
"""

from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


REPO_ROOT = Path(__file__).resolve().parents[1]
SHARED_FILE = REPO_ROOT / ".agent" / "skills" / "_shared" / "__init__.py"
GITHUB_EXPLORER_FILE = REPO_ROOT / ".agent" / "skills" / "github-explorer" / "scripts" / "github_explorer.py"
SKILL_CONVERTER_FILE = REPO_ROOT / ".agent" / "skills" / "skill-converter" / "scripts" / "skill_converter.py"

INDEX_TEMPLATE = """# Agent Skills 索引

## 📦 可用技能一覽

| 技能名稱 | 用途 | 調用指令 |
|----------|------|----------|
| `codex-collaboration-bridge` | IDE Agent 與 Codex CLI 協作橋接 | `cat .agent/skills/codex-collaboration-bridge/SKILL.md` |

---

## 🚧 未來技能 (規劃中)

| 技能名稱 | 用途 | 狀態 |
|----------|------|------|
| `security_scan` | 深度安全漏洞掃描 | ⏳ 規劃中 |
"""

WHITELIST_TEMPLATE = {
    "version": "1.0",
    "approved_sources": ["openai/*"],
    "approval_policy": {
        "auto_approve_official_orgs": True,
        "require_manual_approval_for_personal_repos": True,
        "minimum_stars": 100,
        "maximum_repo_age_months": 6,
    },
}

SKILL_MD_CONTENT = """---
name: gh-address-comments
description: Handle PR comments with gh CLI.
---

# PR Comment Handler

Use gh CLI to inspect and address PR comments.
"""

FETCH_COMMENTS_CONTENT = '''#!/usr/bin/env python3
"""Fetch PR comments with gh CLI."""

import json


def main() -> None:
    print(json.dumps({"ok": True}))


if __name__ == "__main__":
    main()
'''


def load_module(module_name: str, file_path: Path):
    sys.modules.pop(module_name, None)
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"無法載入模組：{file_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


class FakeResponse:
    def __init__(self, status_code: int, text: str) -> None:
        self.status_code = status_code
        self.text = text


class FakeRequests:
    class exceptions:
        Timeout = TimeoutError

    def __init__(self, responses: dict[str, str]) -> None:
        self._responses = responses

    def get(self, url: str, timeout: int = 15, params=None, headers=None):
        text = self._responses.get(url)
        if text is None:
            return FakeResponse(404, "")
        return FakeResponse(200, text)


class ExternalSkillPackageRegressionTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)

        self.workspace_root = Path(self.temp_dir.name)
        self.agent_dir = self.workspace_root / ".agent"
        self.skills_dir = self.workspace_root / ".agent" / "skills"
        self.shared_dir = self.skills_dir / "_shared"
        self.schemas_dir = self.skills_dir / "schemas"
        self.state_skills_dir = self.agent_dir / "state" / "skills"
        self.config_skills_dir = self.agent_dir / "config" / "skills"
        self.local_skills_dir = self.agent_dir / "skills_local"
        self.index_path = self.skills_dir / "INDEX.md"
        self.local_index_path = self.state_skills_dir / "INDEX.local.md"
        self.manifest_path = self.state_skills_dir / "skill_manifest.json"
        self.whitelist_path = self.config_skills_dir / "skill_whitelist.json"
        self.audit_path = self.state_skills_dir / "audit.log"

        self.shared_dir.mkdir(parents=True, exist_ok=True)
        self.schemas_dir.mkdir(parents=True, exist_ok=True)
        self.state_skills_dir.mkdir(parents=True, exist_ok=True)
        self.config_skills_dir.mkdir(parents=True, exist_ok=True)
        self.local_skills_dir.mkdir(parents=True, exist_ok=True)
        self.index_path.write_text(INDEX_TEMPLATE, encoding="utf-8")
        self.manifest_path.write_text(json.dumps({"version": "1.0", "skills": []}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        self.whitelist_path.write_text(json.dumps(WHITELIST_TEMPLATE, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

        self.shared = load_module("_shared", SHARED_FILE)
        self.converter = load_module("test_skill_converter_module", SKILL_CONVERTER_FILE)
        self.github_explorer = load_module("test_github_explorer_module", GITHUB_EXPLORER_FILE)

        self.patches = [
            patch.object(self.shared, "SKILLS_DIR", self.skills_dir),
            patch.object(self.shared, "AGENT_DIR", self.agent_dir),
            patch.object(self.shared, "SHARED_DIR", self.shared_dir),
            patch.object(self.shared, "PUBLIC_SCHEMAS_DIR", self.schemas_dir),
            patch.object(self.shared, "STATE_SKILLS_DIR", self.state_skills_dir),
            patch.object(self.shared, "CONFIG_SKILLS_DIR", self.config_skills_dir),
            patch.object(self.shared, "LOCAL_SKILLS_DIR", self.local_skills_dir),
            patch.object(self.shared, "CANONICAL_MANIFEST_PATH", self.manifest_path),
            patch.object(self.shared, "CANONICAL_WHITELIST_PATH", self.whitelist_path),
            patch.object(self.shared, "AUDIT_LOG_PATH", self.audit_path),
            patch.object(self.shared, "INDEX_PATH", self.index_path),
            patch.object(self.shared, "LOCAL_INDEX_PATH", self.local_index_path),
            patch.object(self.github_explorer, "SKILLS_DIR", self.skills_dir),
            patch.object(self.github_explorer, "AGENT_DIR", self.agent_dir),
            patch.object(self.github_explorer, "AUDIT_LOG_PATH", self.audit_path),
            patch.object(self.github_explorer, "LOCAL_SKILLS_DIR", self.local_skills_dir),
            patch.object(self.github_explorer, "LOCAL_INDEX_PATH", self.local_index_path),
            patch.object(self.converter, "SKILLS_DIR", self.skills_dir),
            patch.object(self.converter, "LOCAL_SKILLS_DIR", self.local_skills_dir),
            patch.object(self.converter, "LOCAL_INDEX_PATH", self.local_index_path),
        ]
        for active_patch in self.patches:
            active_patch.start()
            self.addCleanup(active_patch.stop)

    def raw_url(self, remote_path: str) -> str:
        return f"{self.github_explorer.GITHUB_RAW_BASE}/openai/skills/main/{remote_path}"

    def fake_requests(self) -> FakeRequests:
        return FakeRequests(
            {
                self.raw_url("skills/.curated/gh-address-comments/SKILL.md"): SKILL_MD_CONTENT,
                self.raw_url("skills/.curated/gh-address-comments/scripts/fetch_comments.py"): FETCH_COMMENTS_CONTENT,
            }
        )

    def populate_external_skill(self) -> tuple[dict, dict]:
        fake_requests = self.fake_requests()
        with patch.object(self.github_explorer, "_require_requests", return_value=(fake_requests, fake_requests.exceptions)), patch.object(
            self.github_explorer,
            "_load_skill_converter_module",
            return_value=self.converter,
        ), patch.object(
            self.github_explorer,
            "run_security_scan",
            return_value={
                "status": "warning",
                "issues": [],
                "summary": {
                    "api_key_leak": 0,
                    "file_too_long": 0,
                    "missing_chinese_comment": 0,
                },
            },
        ):
            skill_result = self.github_explorer.download_skill(
                "openai/skills",
                "skills/.curated/gh-address-comments/SKILL.md",
                user_confirmed=True,
            )
            script_result = self.github_explorer.download_skill(
                "openai/skills",
                "skills/.curated/gh-address-comments/scripts/fetch_comments.py",
                user_confirmed=True,
            )
        return skill_result, script_result

    def test_resolver_groups_nested_paths_into_one_package(self) -> None:
        cases = {
            "skills/.curated/gh-address-comments/SKILL.md": "SKILL.md",
            "skills/.curated/gh-address-comments/scripts/fetch_comments.py": "scripts/fetch_comments.py",
            "skills/.curated/gh-address-comments/resources/data/example.json": "resources/data/example.json",
        }

        for remote_path, expected_relative_path in cases.items():
            with self.subTest(remote_path=remote_path):
                layout = self.github_explorer._resolve_external_package_layout("openai/skills", remote_path)
                self.assertEqual(layout["skill_name"], "gh_address_comments")
                self.assertEqual(layout["package_dir_name"], "gh-address-comments")
                self.assertEqual(layout["package_relative_path"], expected_relative_path)

    def test_download_and_converter_preserve_package_relative_path(self) -> None:
        skill_result, script_result = self.populate_external_skill()
        self.assertEqual(skill_result["status"], "success")
        self.assertEqual(script_result["status"], "success")

        package_root = self.local_skills_dir / "gh-address-comments"
        script_path = package_root / "scripts" / "fetch_comments.py"
        self.assertTrue((package_root / "SKILL.md").exists())
        self.assertTrue(script_path.exists())
        self.assertFalse((self.skills_dir / "scripts").exists())

        script_content = script_path.read_text(encoding="utf-8")
        self.assertIn(".agent/skills_local/gh-address-comments/scripts/fetch_comments.py", script_content)

        core_index_content = self.index_path.read_text(encoding="utf-8")
        self.assertNotIn("gh_address_comments", core_index_content)
        self.assertNotIn("gh-address-comments", core_index_content)

        local_index_content = self.local_index_path.read_text(encoding="utf-8")
        self.assertIn("python .agent/skills_local/gh-address-comments/scripts/fetch_comments.py", local_index_content)

        manifest = json.loads(self.manifest_path.read_text(encoding="utf-8"))
        entry = next(item for item in manifest["skills"] if item["name"] == "gh_address_comments")
        self.assertEqual(entry["package_path"], ".agent/skills_local/gh-address-comments")
        self.assertEqual(entry["path"], ".agent/skills_local/gh-address-comments/scripts/fetch_comments.py")

    def test_rollback_cleans_package_manifest_and_index(self) -> None:
        self.populate_external_skill()

        result = self.github_explorer.rollback_skill("gh_address_comments")

        self.assertEqual(result["status"], "success")
        self.assertIn("已從 INDEX.local.md 移除", result["actions_taken"])
        self.assertFalse((self.local_skills_dir / "gh-address-comments").exists())

        manifest = json.loads(self.manifest_path.read_text(encoding="utf-8"))
        self.assertEqual([item for item in manifest["skills"] if item.get("type") == "external"], [])

        core_index_content = self.index_path.read_text(encoding="utf-8")
        self.assertNotIn("gh_address_comments", core_index_content)
        self.assertNotIn("gh-address-comments", core_index_content)

        local_index_content = self.local_index_path.read_text(encoding="utf-8")
        self.assertNotIn("gh_address_comments", local_index_content)
        self.assertNotIn("gh-address-comments", local_index_content)


if __name__ == "__main__":
    unittest.main()
