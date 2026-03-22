# -*- coding: utf-8 -*-
"""
tests/test_reviewed_sync_manager_skill.py
=======================================
用途：驗證 reviewed-sync-manager 的 writer / promotion 兩段式流程。
"""

from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_FILE = REPO_ROOT / ".agent" / "skills" / "reviewed-sync-manager" / "scripts" / "reviewed_sync_manager.py"


def load_module(module_name: str, file_path: Path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"無法載入模組：{file_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def build_vault(root: Path) -> Path:
    vault_root = root / "ObsidianVault"
    (vault_root / "00-indexes").mkdir(parents=True)
    (vault_root / "10-inbox" / "reviewed-sync-candidates").mkdir(parents=True)
    (vault_root / "20-reviewed" / "agent-workflow-template" / "workflow-knowledge").mkdir(parents=True)
    (vault_root / "30-archives" / "superseded").mkdir(parents=True)
    return vault_root


class ReviewedSyncManagerSkillTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tool = load_module("test_reviewed_sync_manager_module", SCRIPT_FILE)

    def test_write_candidate_from_repo_file_creates_candidate_note(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            vault_root = build_vault(Path(temp_dir))
            payload = {
                "title": "obsidian sync policy summary",
                "source_repo": "agent-workflow-template",
                "source_path": "maintainers/chat/2026-03-20-project-maintainers-obsidian-sync-policy.md",
                "source_type": "repo-file",
                "summary_text": "整理 reviewed-sync policy 的核心結論。",
                "target_reviewed_dir": "agent-workflow-template/workflow-knowledge",
            }

            result = self.tool.write_candidate(vault_root, payload)

            created_path = Path(result["target_note"])
            content = created_path.read_text(encoding="utf-8")

        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["action"], "create")
        self.assertIn("note_kind: reviewed-sync-candidate", content)
        self.assertIn("payload_schema_version: reviewed-sync-candidate.v1", content)
        self.assertIn("promotion_status: promotion-candidate", content)
        self.assertIn("# Summary", content)

    def test_validate_json_payload_contract_rejects_unknown_field(self) -> None:
        payload = {
            "schema_version": "reviewed-sync-candidate.v1",
            "title": "obsidian sync policy summary",
            "source_repo": "agent-workflow-template",
            "source_path": "maintainers/chat/2026-03-20-project-maintainers-obsidian-sync-policy.md",
            "source_type": "repo-file",
            "summary_text": "整理 reviewed-sync policy 的核心結論。",
            "target_reviewed_dir": "agent-workflow-template/workflow-knowledge",
            "unexpected_field": "should fail",
        }

        with self.assertRaises(ValueError):
            self.tool.validate_json_payload_contract(payload)

    def test_validate_json_payload_contract_rejects_wrong_list_type(self) -> None:
        payload = {
            "schema_version": "reviewed-sync-candidate.v1",
            "title": "obsidian sync policy summary",
            "source_repo": "agent-workflow-template",
            "source_path": "maintainers/chat/2026-03-20-project-maintainers-obsidian-sync-policy.md",
            "source_type": "repo-file",
            "summary_text": "整理 reviewed-sync policy 的核心結論。",
            "target_reviewed_dir": "agent-workflow-template/workflow-knowledge",
            "index_targets": "workflows.md",
        }

        with self.assertRaises(ValueError):
            self.tool.validate_json_payload_contract(payload)

    def test_write_candidate_from_manual_summary_updates_existing_candidate(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            vault_root = build_vault(Path(temp_dir))
            payload = {
                "title": "obsidian mount governance summary",
                "source_repo": "agent-workflow-template",
                "source_path": "manual-summary",
                "source_type": "manual-summary",
                "summary_text": "第一版整理。",
                "target_reviewed_dir": "agent-workflow-template/maintainer-sops",
            }
            first = self.tool.write_candidate(vault_root, payload)

            payload["summary_text"] = "第二版整理。"
            second = self.tool.write_candidate(vault_root, payload)

            content = Path(second["target_note"]).read_text(encoding="utf-8")

        self.assertEqual(first["target_note"], second["target_note"])
        self.assertEqual(second["action"], "update")
        self.assertIn("第二版整理。", content)

    def test_promote_candidate_creates_reviewed_note_and_updates_index(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            vault_root = build_vault(Path(temp_dir))
            candidate = self.tool.write_candidate(
                vault_root,
                {
                    "title": "reviewed sync policy summary",
                    "source_repo": "agent-workflow-template",
                    "source_path": "maintainers/chat/2026-03-20-project-maintainers-obsidian-sync-policy.md",
                    "source_type": "maintainer-policy",
                    "summary_text": "整理 reviewed-sync 邊界與 repo-first 原則。",
                    "target_reviewed_dir": "agent-workflow-template/workflow-knowledge",
                    "index_targets": ["workflows.md"],
                },
            )

            result = self.tool.promote_candidate(vault_root, Path(candidate["target_note"]))

            target_path = Path(result["target_note"])
            content = target_path.read_text(encoding="utf-8")
            workflows_index = (vault_root / "00-indexes" / "workflows.md").read_text(encoding="utf-8")
            target_exists = target_path.exists()

        self.assertEqual(result["action"], "promote")
        self.assertTrue(target_exists)
        self.assertIn("note_kind: reviewed-note", content)
        self.assertIn("review_status: approved", content)
        self.assertIn("promotion_status: reviewed", content)
        self.assertIn("reviewed sync policy summary", workflows_index)

    def test_promote_candidate_merges_duplicate_reviewed_note_and_archives_candidate(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            vault_root = build_vault(Path(temp_dir))
            first_candidate = self.tool.write_candidate(
                vault_root,
                {
                    "title": "obsidian workflow summary",
                    "source_repo": "agent-workflow-template",
                    "source_path": "maintainers/chat/2026-03-20-obsidian-vault-structure-and-frontmatter.md",
                    "source_type": "maintainer-analysis",
                    "summary_text": "第一版 reviewed summary。",
                    "target_reviewed_dir": "agent-workflow-template/workflow-knowledge",
                },
            )
            first_promote = self.tool.promote_candidate(vault_root, Path(first_candidate["target_note"]))

            second_candidate = self.tool.write_candidate(
                vault_root,
                {
                    "title": "obsidian workflow summary",
                    "source_repo": "agent-workflow-template",
                    "source_path": "maintainers/chat/2026-03-20-obsidian-vault-structure-and-frontmatter.md",
                    "source_type": "maintainer-analysis",
                    "summary_text": "第二版 reviewed summary。",
                    "target_reviewed_dir": "agent-workflow-template/workflow-knowledge",
                },
            )
            second_promote = self.tool.promote_candidate(vault_root, Path(second_candidate["target_note"]))

            archived_path = Path(second_promote["archived_candidate"])
            archived_exists = archived_path.exists()
            archived_parent = str(archived_path.parent)

        self.assertEqual(second_promote["action"], "merge")
        self.assertEqual(first_promote["target_note"], second_promote["target_note"])
        self.assertTrue(archived_exists)
        self.assertIn("30-archives/superseded", archived_parent)

    def test_promote_candidate_merge_does_not_duplicate_existing_index_link(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            vault_root = build_vault(Path(temp_dir))
            first_candidate = self.tool.write_candidate(
                vault_root,
                {
                    "title": "obsidian workflow summary",
                    "source_repo": "agent-workflow-template",
                    "source_path": "maintainers/chat/2026-03-20-obsidian-vault-structure-and-frontmatter.md",
                    "source_type": "maintainer-analysis",
                    "summary_text": "第一版 reviewed summary。",
                    "target_reviewed_dir": "agent-workflow-template/workflow-knowledge",
                    "index_targets": ["workflows.md"],
                },
            )
            first_promote = self.tool.promote_candidate(vault_root, Path(first_candidate["target_note"]))

            second_candidate = self.tool.write_candidate(
                vault_root,
                {
                    "title": "obsidian workflow summary",
                    "source_repo": "agent-workflow-template",
                    "source_path": "maintainers/chat/2026-03-20-obsidian-vault-structure-and-frontmatter.md",
                    "source_type": "maintainer-analysis",
                    "summary_text": "第二版 reviewed summary。",
                    "target_reviewed_dir": "agent-workflow-template/workflow-knowledge",
                    "index_targets": ["workflows.md"],
                },
            )
            second_promote = self.tool.promote_candidate(vault_root, Path(second_candidate["target_note"]))

            target_note = Path(first_promote["target_note"])
            wiki_link = f"[[{target_note.relative_to(vault_root).with_suffix('').as_posix()}|obsidian workflow summary]]"
            workflows_index = (vault_root / "00-indexes" / "workflows.md").read_text(encoding="utf-8")

        self.assertEqual(second_promote["action"], "merge")
        self.assertEqual(second_promote["updated_indexes"], [])
        self.assertEqual(workflows_index.count(wiki_link), 1)

    def test_promote_candidate_archives_with_suffix_when_archive_name_collides(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            vault_root = build_vault(Path(temp_dir))
            first_candidate = self.tool.write_candidate(
                vault_root,
                {
                    "title": "archive collision summary",
                    "source_repo": "agent-workflow-template",
                    "source_path": "maintainers/chat/2026-03-20-project-maintainers-obsidian-sync-policy.md",
                    "source_type": "maintainer-policy",
                    "summary_text": "第一版 reviewed summary。",
                    "target_reviewed_dir": "agent-workflow-template/workflow-knowledge",
                },
            )
            self.tool.promote_candidate(vault_root, Path(first_candidate["target_note"]))

            second_candidate = self.tool.write_candidate(
                vault_root,
                {
                    "title": "archive collision summary",
                    "source_repo": "agent-workflow-template",
                    "source_path": "maintainers/chat/2026-03-20-project-maintainers-obsidian-sync-policy.md",
                    "source_type": "maintainer-policy",
                    "summary_text": "第二版 reviewed summary。",
                    "target_reviewed_dir": "agent-workflow-template/workflow-knowledge",
                },
            )
            second_candidate_path = Path(second_candidate["target_note"])
            archive_dir = vault_root / "30-archives" / "superseded"
            archive_dir.mkdir(parents=True, exist_ok=True)
            collision_path = archive_dir / second_candidate_path.name
            collision_path.write_text("existing archive\n", encoding="utf-8")

            second_promote = self.tool.promote_candidate(vault_root, second_candidate_path)
            archived_path = Path(second_promote["archived_candidate"])
            archived_exists = archived_path.exists()
            archived_name = archived_path.name

        self.assertEqual(second_promote["action"], "merge")
        self.assertTrue(archived_exists)
        self.assertNotEqual(archived_name, second_candidate_path.name)
        self.assertTrue(archived_name.startswith(second_candidate_path.stem + "-"))

    def test_tool_rejects_non_template_repo(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            vault_root = build_vault(Path(temp_dir))
            fake_repo = Path(temp_dir) / "downstream-repo"
            fake_repo.mkdir(parents=True)

            with self.assertRaises(RuntimeError):
                self.tool.write_candidate(
                    vault_root,
                    {
                        "title": "should fail",
                        "source_repo": "demo-project",
                        "source_path": "manual-summary",
                        "source_type": "manual-summary",
                        "summary_text": "not allowed",
                        "target_reviewed_dir": "agent-workflow-template/workflow-knowledge",
                    },
                    repo_root=fake_repo,
                )


if __name__ == "__main__":
    unittest.main()
