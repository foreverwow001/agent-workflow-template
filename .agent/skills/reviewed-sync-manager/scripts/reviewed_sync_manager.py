# -*- coding: utf-8 -*-
"""
.agent/skills/reviewed-sync-manager/scripts/reviewed_sync_manager.py
====================================================================
用途：在 workflow template repo 中管理 Obsidian reviewed-sync candidate writer 與 promotion 流程。
職責：
  - 將候選整理稿寫入 reviewed-sync-candidates
  - 將已確認 candidate promotion 到 20-reviewed
  - promotion 時補齊 frontmatter、更新 index 與做 dedupe
  - 明確阻擋 downstream project repo 使用本工具
====================================================================
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple


REPO_ROOT = Path(__file__).resolve().parents[4]
CANDIDATES_REL = Path("10-inbox") / "reviewed-sync-candidates"
REVIEWED_REL = Path("20-reviewed")
ARCHIVE_REL = Path("30-archives") / "superseded"
INDEXES_REL = Path("00-indexes")

DEFAULT_SOURCE_REPO = "agent-workflow-template"
DEFAULT_REVIEWED_BY = "human"
PAYLOAD_SCHEMA_VERSION = "reviewed-sync-candidate.v1"

REQUIRED_JSON_PAYLOAD_FIELDS = (
    "schema_version",
    "title",
    "source_repo",
    "source_path",
    "source_type",
    "summary_text",
    "target_reviewed_dir",
)

OPTIONAL_JSON_PAYLOAD_FIELDS = (
    "index_targets",
    "why_in_inbox",
    "reusability_check",
    "next_review_action",
    "source_notes",
    "source_excerpt",
    "tags",
    "related_topics",
    "related_projects",
    "candidate_source_mode",
    "candidate_key",
    "reviewed_key",
    "synced_on",
)

LIST_PAYLOAD_FIELDS = (
    "index_targets",
    "why_in_inbox",
    "reusability_check",
    "next_review_action",
    "source_notes",
    "tags",
    "related_topics",
    "related_projects",
)

STRING_PAYLOAD_FIELDS = (
    "schema_version",
    "title",
    "source_repo",
    "source_path",
    "source_type",
    "summary_text",
    "target_reviewed_dir",
    "source_excerpt",
    "candidate_source_mode",
    "candidate_key",
    "reviewed_key",
    "synced_on",
)

ALLOWED_PAYLOAD_FIELDS = set(REQUIRED_JSON_PAYLOAD_FIELDS) | set(OPTIONAL_JSON_PAYLOAD_FIELDS)


def today_iso() -> str:
    return datetime.now(UTC).date().isoformat()


def now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def slugify(value: str, max_length: int = 80) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.strip().lower())
    slug = re.sub(r"-+", "-", slug).strip("-")
    if not slug:
        slug = "note"
    return slug[:max_length].rstrip("-")


def parse_scalar(value: str) -> Any:
    stripped = value.strip()
    if stripped in {"true", "True"}:
        return True
    if stripped in {"false", "False"}:
        return False
    if re.fullmatch(r"-?\d+", stripped):
        return int(stripped)
    if (stripped.startswith('"') and stripped.endswith('"')) or (stripped.startswith("'") and stripped.endswith("'")):
        return stripped[1:-1]
    return stripped


def validate_payload_keys(payload: Dict[str, Any]) -> None:
    unknown_fields = sorted(set(payload) - ALLOWED_PAYLOAD_FIELDS)
    if unknown_fields:
        joined = ", ".join(unknown_fields)
        raise ValueError(f"payload 含未支援欄位：{joined}")


def require_non_empty_string(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"payload 欄位 `{field_name}` 必須是非空字串")
    return value.strip()


def normalize_payload_string_field(payload: Dict[str, Any], field_name: str, default: str = "") -> str:
    value = payload.get(field_name, default)
    if value is None:
        value = default
    if not isinstance(value, str):
        raise ValueError(f"payload 欄位 `{field_name}` 必須是字串")
    return value.strip()


def normalize_payload_list_field(payload: Dict[str, Any], field_name: str) -> List[str]:
    value = payload.get(field_name)
    if value is None:
        return []
    if not isinstance(value, list):
        raise ValueError(f"payload 欄位 `{field_name}` 必須是字串陣列")
    items = [str(item).strip() for item in value if str(item).strip()]
    return dedupe_preserve_order(items)


def validate_json_payload_contract(payload: Dict[str, Any]) -> None:
    validate_payload_keys(payload)

    for field_name in REQUIRED_JSON_PAYLOAD_FIELDS:
        require_non_empty_string(payload.get(field_name), field_name)

    if payload.get("schema_version") != PAYLOAD_SCHEMA_VERSION:
        raise ValueError(
            f"schema_version 必須是 `{PAYLOAD_SCHEMA_VERSION}`，目前收到 `{payload.get('schema_version')}`"
        )

    for field_name in STRING_PAYLOAD_FIELDS:
        if field_name in payload and payload[field_name] is not None and not isinstance(payload[field_name], str):
            raise ValueError(f"payload 欄位 `{field_name}` 必須是字串")

    for field_name in LIST_PAYLOAD_FIELDS:
        if field_name in payload and payload[field_name] is not None and not isinstance(payload[field_name], list):
            raise ValueError(f"payload 欄位 `{field_name}` 必須是字串陣列")


def parse_frontmatter(text: str) -> Tuple[Dict[str, Any], str]:
    if not text.startswith("---\n"):
        return {}, text

    lines = text.splitlines()
    try:
        closing_index = lines[1:].index("---") + 1
    except ValueError:
        return {}, text

    frontmatter_lines = lines[1:closing_index]
    body = "\n".join(lines[closing_index + 1 :]).lstrip("\n")

    data: Dict[str, Any] = {}
    index = 0
    while index < len(frontmatter_lines):
        line = frontmatter_lines[index]
        if not line.strip() or ":" not in line:
            index += 1
            continue
        key, raw_value = line.split(":", 1)
        key = key.strip()
        raw_value = raw_value.strip()
        if raw_value:
            data[key] = parse_scalar(raw_value)
            index += 1
            continue

        list_values: List[Any] = []
        nested_index = index + 1
        while nested_index < len(frontmatter_lines):
            nested = frontmatter_lines[nested_index]
            if nested.startswith("  - "):
                list_values.append(parse_scalar(nested[4:]))
                nested_index += 1
                continue
            if not nested.strip():
                nested_index += 1
                continue
            break
        data[key] = list_values
        index = nested_index

    return data, body


def render_scalar(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def render_frontmatter(frontmatter: Dict[str, Any]) -> str:
    lines = ["---"]
    for key, value in frontmatter.items():
        if isinstance(value, list):
            lines.append(f"{key}:")
            for item in value:
                lines.append(f"  - {item}")
        else:
            lines.append(f"{key}: {render_scalar(value)}")
    lines.append("---")
    return "\n".join(lines)


def ensure_list(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    if isinstance(value, str):
        return [value] if value.strip() else []
    return [str(value)]


def dedupe_preserve_order(values: Iterable[str]) -> List[str]:
    seen: set[str] = set()
    ordered: List[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            ordered.append(value)
    return ordered


def format_bullet_section(values: Any, fallback: str) -> str:
    items = ensure_list(values)
    if not items:
        items = [fallback]
    return "\n".join(f"- {item}" for item in items)


def relative_to_repo(path: Path, repo_root: Path) -> str:
    return path.resolve().relative_to(repo_root.resolve()).as_posix()


def normalize_target_reviewed_dir(value: str) -> str:
    cleaned = value.strip().strip("/")
    if cleaned.startswith("20-reviewed/"):
        cleaned = cleaned[len("20-reviewed/") :]
    if not cleaned:
        raise ValueError("target_reviewed_dir 不可為空")
    if cleaned.startswith("../") or cleaned == "..":
        raise ValueError("target_reviewed_dir 不可跳出 20-reviewed")
    return cleaned


def normalize_index_target(value: str) -> str:
    cleaned = value.strip().strip("/")
    if cleaned.startswith("00-indexes/"):
        cleaned = cleaned[len("00-indexes/") :]
    if not cleaned:
        raise ValueError("index target 不可為空")
    if not cleaned.endswith(".md"):
        cleaned = f"{cleaned}.md"
    return cleaned


def default_index_targets(target_reviewed_dir: str) -> List[str]:
    if target_reviewed_dir.startswith("agent-workflow-template/workflow-knowledge"):
        return ["workflows.md"]
    if target_reviewed_dir.startswith("agent-workflow-template/maintainer-sops"):
        return ["workflows.md"]
    if target_reviewed_dir.startswith("lessons-learned"):
        return ["topics.md"]
    return ["projects.md"]


def build_candidate_key(payload: Dict[str, Any]) -> str:
    return "|".join(
        [
            str(payload.get("source_repo", DEFAULT_SOURCE_REPO)).strip(),
            str(payload.get("source_path", "manual-summary")).strip(),
            str(payload.get("source_type", "manual-summary")).strip(),
            str(payload.get("target_reviewed_dir", "")).strip(),
            str(payload.get("title", "")).strip(),
        ]
    )


def build_reviewed_key(payload: Dict[str, Any]) -> str:
    return "|".join(
        [
            str(payload.get("source_repo", DEFAULT_SOURCE_REPO)).strip(),
            str(payload.get("source_path", "manual-summary")).strip(),
            str(payload.get("target_reviewed_dir", "")).strip(),
            str(payload.get("title", "")).strip(),
        ]
    )


def build_candidate_filename(payload: Dict[str, Any], candidates_dir: Path) -> str:
    base = f"{today_iso()}-candidate-{slugify(str(payload.get('title', 'candidate')))}"
    candidate = f"{base}.md"
    counter = 2
    while (candidates_dir / candidate).exists():
        candidate = f"{base}-{counter}.md"
        counter += 1
    return candidate


def build_reviewed_filename(frontmatter: Dict[str, Any], target_dir: Path) -> str:
    base = f"{today_iso()}-{slugify(str(frontmatter.get('title', 'reviewed-note')))}"
    candidate = f"{base}.md"
    counter = 2
    while (target_dir / candidate).exists():
        candidate = f"{base}-{counter}.md"
        counter += 1
    return candidate


def is_workflow_template_repo(repo_root: Path) -> bool:
    return (
        (repo_root / ".agent" / "workflow_baseline_rules.md").exists()
        and (repo_root / "maintainers" / "chat" / "2026-03-20-project-maintainers-obsidian-sync-policy.md").exists()
    )


def ensure_workflow_template_repo(repo_root: Path) -> None:
    if not is_workflow_template_repo(repo_root):
        raise RuntimeError("reviewed-sync-manager 只能在 workflow template repo 中執行")


def resolve_vault_root(vault_root: str | None, repo_root: Path) -> Path:
    if vault_root:
        return Path(vault_root)
    env_value = os.environ.get("OBSIDIAN_VAULT_ROOT")
    if env_value:
        return Path(env_value)
    fallback = repo_root / "obsidian-vault"
    if fallback.exists():
        return fallback
    raise RuntimeError("找不到 vault root；請提供 --vault-root 或設定 OBSIDIAN_VAULT_ROOT")


def list_note_files(root_dir: Path) -> List[Path]:
    if not root_dir.exists():
        return []
    return sorted(path for path in root_dir.rglob("*.md") if path.is_file())


def find_note_by_key(root_dir: Path, key_name: str, key_value: str, note_kind: str | None = None) -> List[Dict[str, Any]]:
    matches: List[Dict[str, Any]] = []
    for note_path in list_note_files(root_dir):
        frontmatter, body = parse_frontmatter(note_path.read_text(encoding="utf-8"))
        if not frontmatter:
            continue
        if note_kind and frontmatter.get("note_kind") != note_kind:
            continue
        if str(frontmatter.get(key_name, "")).strip() == key_value:
            matches.append({"path": note_path, "frontmatter": frontmatter, "body": body})
    return sorted(matches, key=lambda item: str(item["path"]))


def create_index_file(index_path: Path) -> None:
    title = index_path.stem.replace("-", " ")
    frontmatter = {
        "title": title,
        "source_repo": "none",
        "source_path": "none",
        "source_type": "index",
        "review_status": "approved",
        "promotion_status": "reviewed",
        "synced_on": today_iso(),
        "tags": ["index", "workflow", "knowledge-map"],
    }
    body = f"# {title.title()}\n\n## Reviewed Sync Entries\n\n"
    index_path.parent.mkdir(parents=True, exist_ok=True)
    index_path.write_text(f"{render_frontmatter(frontmatter)}\n\n{body}", encoding="utf-8")


def update_index_file(index_path: Path, note_path: Path, vault_root: Path, title: str) -> bool:
    if not index_path.exists():
        create_index_file(index_path)

    rel_note = note_path.relative_to(vault_root).with_suffix("").as_posix()
    wiki_link = f"[[{rel_note}|{title}]]"

    content = index_path.read_text(encoding="utf-8")
    if wiki_link in content:
        return False

    marker = "## Reviewed Sync Entries"
    addition = f"- {wiki_link}\n"
    if marker in content:
        content = content.rstrip() + "\n" + addition
    else:
        content = content.rstrip() + f"\n\n{marker}\n\n{addition}"
    index_path.write_text(content, encoding="utf-8")
    return True


def archive_candidate(candidate_path: Path, vault_root: Path) -> Path:
    archive_dir = vault_root / ARCHIVE_REL
    archive_dir.mkdir(parents=True, exist_ok=True)
    target = archive_dir / candidate_path.name
    counter = 2
    while target.exists():
        target = archive_dir / f"{candidate_path.stem}-{counter}{candidate_path.suffix}"
        counter += 1
    candidate_path.replace(target)
    return target


def load_json_payload(payload_file: str | None, use_stdin: bool = False) -> Dict[str, Any]:
    if payload_file:
        return json.loads(Path(payload_file).read_text(encoding="utf-8"))
    if use_stdin:
        return json.loads(sys.stdin.read())
    raise ValueError("缺少 JSON payload 來源")


def build_source_excerpt(source_file: Path, max_lines: int) -> str:
    lines = source_file.read_text(encoding="utf-8").splitlines()
    excerpt = lines[:max_lines]
    if len(lines) > max_lines:
        excerpt.append("...")
    return "\n".join(excerpt)


def summarize_title_from_text(text: str) -> str:
    line = next((line.strip() for line in text.splitlines() if line.strip()), "manual summary")
    return line[:80]


def normalize_candidate_payload(payload: Dict[str, Any], repo_root: Path) -> Dict[str, Any]:
    validate_payload_keys(payload)

    normalized: Dict[str, Any] = {}
    normalized["schema_version"] = normalize_payload_string_field(payload, "schema_version", PAYLOAD_SCHEMA_VERSION) or PAYLOAD_SCHEMA_VERSION
    if normalized["schema_version"] != PAYLOAD_SCHEMA_VERSION:
        raise ValueError(f"schema_version 不支援：{normalized['schema_version']}")

    normalized["source_repo"] = normalize_payload_string_field(payload, "source_repo", DEFAULT_SOURCE_REPO) or DEFAULT_SOURCE_REPO
    normalized["source_path"] = normalize_payload_string_field(payload, "source_path", "manual-summary") or "manual-summary"
    normalized["source_type"] = normalize_payload_string_field(payload, "source_type", "manual-summary") or "manual-summary"
    normalized["summary_text"] = normalize_payload_string_field(payload, "summary_text", "")
    normalized["title"] = normalize_payload_string_field(
        payload,
        "title",
        summarize_title_from_text(normalized["summary_text"] or "manual summary"),
    )
    target_reviewed_dir = payload.get("target_reviewed_dir")
    if not target_reviewed_dir:
        raise ValueError("缺少 target_reviewed_dir")
    normalized["target_reviewed_dir"] = normalize_target_reviewed_dir(str(target_reviewed_dir))
    index_targets = normalize_payload_list_field(payload, "index_targets") or default_index_targets(normalized["target_reviewed_dir"])
    normalized["index_targets"] = dedupe_preserve_order(normalize_index_target(item) for item in index_targets)
    normalized["why_in_inbox"] = normalize_payload_list_field(payload, "why_in_inbox")
    normalized["reusability_check"] = normalize_payload_list_field(payload, "reusability_check")
    normalized["next_review_action"] = normalize_payload_list_field(payload, "next_review_action")
    normalized["source_notes"] = normalize_payload_list_field(payload, "source_notes")
    normalized["source_excerpt"] = normalize_payload_string_field(payload, "source_excerpt", "")
    normalized["tags"] = normalize_payload_list_field(payload, "tags") or ["inbox", "candidate", "reviewed-sync"]
    normalized["related_topics"] = normalize_payload_list_field(payload, "related_topics")
    normalized["related_projects"] = normalize_payload_list_field(payload, "related_projects") or [DEFAULT_SOURCE_REPO]
    normalized["candidate_source_mode"] = normalize_payload_string_field(
        payload,
        "candidate_source_mode",
        normalized["source_type"],
    ) or normalized["source_type"]
    normalized["candidate_key"] = normalize_payload_string_field(payload, "candidate_key", build_candidate_key(normalized)) or build_candidate_key(normalized)
    normalized["reviewed_key"] = normalize_payload_string_field(payload, "reviewed_key", build_reviewed_key(normalized)) or build_reviewed_key(normalized)
    normalized["synced_on"] = normalize_payload_string_field(payload, "synced_on", today_iso()) or today_iso()
    return normalized


def build_payload_from_source_file(args: argparse.Namespace, repo_root: Path) -> Dict[str, Any]:
    source_file = Path(args.source_file)
    if not source_file.is_absolute():
        source_file = repo_root / source_file
    if not source_file.exists():
        raise FileNotFoundError(f"source file 不存在：{source_file}")

    summary_text = str(args.summary_text or "")
    if args.summary_file:
        summary_text = Path(args.summary_file).read_text(encoding="utf-8")
    if not summary_text.strip():
        summary_text = f"整理 `{relative_to_repo(source_file, repo_root)}` 的 reviewed-sync 候選摘要。"

    return {
        "schema_version": PAYLOAD_SCHEMA_VERSION,
        "title": args.title or source_file.stem.replace("-", " "),
        "source_repo": args.source_repo,
        "source_path": relative_to_repo(source_file, repo_root),
        "source_type": args.source_type or "repo-file",
        "summary_text": summary_text,
        "target_reviewed_dir": args.target_reviewed_dir,
        "index_targets": args.index_target,
        "why_in_inbox": args.why_in_inbox,
        "reusability_check": args.reusability_check,
        "next_review_action": args.next_review_action,
        "source_notes": [f"repo file: {relative_to_repo(source_file, repo_root)}"],
        "source_excerpt": build_source_excerpt(source_file, args.source_excerpt_max_lines),
        "tags": args.tag,
        "related_topics": args.related_topic,
        "related_projects": args.related_project,
        "candidate_source_mode": "repo-file",
    }


def build_payload_from_summary(args: argparse.Namespace) -> Dict[str, Any]:
    summary_text = str(args.summary_text or "")
    if args.summary_file:
        summary_text = Path(args.summary_file).read_text(encoding="utf-8")
    if not summary_text.strip():
        raise ValueError("manual summary 不可為空")

    return {
        "schema_version": PAYLOAD_SCHEMA_VERSION,
        "title": args.title or summarize_title_from_text(summary_text),
        "source_repo": args.source_repo,
        "source_path": args.source_path or "manual-summary",
        "source_type": args.source_type or "manual-summary",
        "summary_text": summary_text,
        "target_reviewed_dir": args.target_reviewed_dir,
        "index_targets": args.index_target,
        "why_in_inbox": args.why_in_inbox,
        "reusability_check": args.reusability_check,
        "next_review_action": args.next_review_action,
        "source_notes": args.source_note,
        "tags": args.tag,
        "related_topics": args.related_topic,
        "related_projects": args.related_project,
        "candidate_source_mode": "manual-summary",
    }


def build_candidate_body(payload: Dict[str, Any]) -> str:
    body = (
        "# Summary\n\n"
        f"{payload['summary_text']}\n\n"
        "# Why This Is In Inbox\n\n"
        f"{format_bullet_section(payload.get('why_in_inbox'), '待人工 review 後決定是否晉升。')}\n\n"
        "# Reusability Check\n\n"
        f"{format_bullet_section(payload.get('reusability_check'), '待補 reusable assessment。')}\n\n"
        "# Target Reviewed Path\n\n"
        f"- 20-reviewed/{payload['target_reviewed_dir']}\n\n"
        "# Source Notes\n\n"
        f"{format_bullet_section(payload.get('source_notes'), '待補來源說明。')}\n"
    )
    if payload.get("source_excerpt"):
        body += f"\n# Source Excerpt\n\n```markdown\n{payload['source_excerpt']}\n```\n"
    body += (
        "\n# Next Review Action\n\n"
        f"{format_bullet_section(payload.get('next_review_action'), '待決定是否 promotion。')}\n"
    )
    return body


def build_candidate_frontmatter(payload: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "title": payload["title"],
        "note_kind": "reviewed-sync-candidate",
        "payload_schema_version": payload["schema_version"],
        "source_repo": payload["source_repo"],
        "source_path": payload["source_path"],
        "source_type": payload["source_type"],
        "review_status": "pending",
        "promotion_status": "promotion-candidate",
        "synced_on": payload.get("synced_on") or today_iso(),
        "target_reviewed_dir": payload["target_reviewed_dir"],
        "index_targets": payload["index_targets"],
        "candidate_key": payload["candidate_key"],
        "reviewed_key": payload["reviewed_key"],
        "candidate_source_mode": payload["candidate_source_mode"],
        "tags": payload["tags"],
        "related_topics": payload["related_topics"],
        "related_projects": payload["related_projects"],
    }


def merge_candidate_frontmatter(existing: Dict[str, Any], payload: Dict[str, Any]) -> Dict[str, Any]:
    merged = dict(existing)
    merged["title"] = payload["title"]
    merged["payload_schema_version"] = payload["schema_version"]
    merged["source_repo"] = payload["source_repo"]
    merged["source_path"] = payload["source_path"]
    merged["source_type"] = payload["source_type"]
    merged["review_status"] = "pending"
    merged["promotion_status"] = "promotion-candidate"
    merged["synced_on"] = today_iso()
    merged["target_reviewed_dir"] = payload["target_reviewed_dir"]
    merged["index_targets"] = dedupe_preserve_order(ensure_list(existing.get("index_targets")) + payload["index_targets"])
    merged["candidate_key"] = payload["candidate_key"]
    merged["reviewed_key"] = payload["reviewed_key"]
    merged["candidate_source_mode"] = payload["candidate_source_mode"]
    merged["tags"] = dedupe_preserve_order(ensure_list(existing.get("tags")) + payload["tags"])
    merged["related_topics"] = dedupe_preserve_order(ensure_list(existing.get("related_topics")) + payload["related_topics"])
    merged["related_projects"] = dedupe_preserve_order(ensure_list(existing.get("related_projects")) + payload["related_projects"])
    return merged


def write_candidate(vault_root: Path, payload: Dict[str, Any], repo_root: Path | None = None) -> Dict[str, Any]:
    repo_root = repo_root or REPO_ROOT
    ensure_workflow_template_repo(repo_root)
    normalized = normalize_candidate_payload(payload, repo_root)
    candidates_dir = vault_root / CANDIDATES_REL
    candidates_dir.mkdir(parents=True, exist_ok=True)

    matches = find_note_by_key(candidates_dir, "candidate_key", normalized["candidate_key"], note_kind="reviewed-sync-candidate")
    body = build_candidate_body(normalized)

    if matches:
        chosen = matches[0]
        merged = merge_candidate_frontmatter(chosen["frontmatter"], normalized)
        chosen["path"].write_text(f"{render_frontmatter(merged)}\n\n{body.rstrip()}\n", encoding="utf-8")
        return {
            "status": "ok",
            "action": "update",
            "target_note": str(chosen["path"]),
            "candidate_key": normalized["candidate_key"],
            "reviewed_key": normalized["reviewed_key"],
        }

    filename = build_candidate_filename(normalized, candidates_dir)
    note_path = candidates_dir / filename
    frontmatter = build_candidate_frontmatter(normalized)
    note_path.write_text(f"{render_frontmatter(frontmatter)}\n\n{body.rstrip()}\n", encoding="utf-8")
    return {
        "status": "ok",
        "action": "create",
        "target_note": str(note_path),
        "candidate_key": normalized["candidate_key"],
        "reviewed_key": normalized["reviewed_key"],
    }


def build_reviewed_frontmatter(candidate_frontmatter: Dict[str, Any], reviewed_by: str) -> Dict[str, Any]:
    return {
        "title": candidate_frontmatter["title"],
        "note_kind": "reviewed-note",
        "payload_schema_version": candidate_frontmatter.get("payload_schema_version", PAYLOAD_SCHEMA_VERSION),
        "source_repo": candidate_frontmatter["source_repo"],
        "source_path": candidate_frontmatter["source_path"],
        "source_type": candidate_frontmatter["source_type"],
        "review_status": "approved",
        "promotion_status": "reviewed",
        "synced_on": today_iso(),
        "source_date": candidate_frontmatter.get("synced_on") or today_iso(),
        "reviewed_by": reviewed_by,
        "reviewed_key": candidate_frontmatter["reviewed_key"],
        "index_targets": dedupe_preserve_order(ensure_list(candidate_frontmatter.get("index_targets"))),
        "tags": dedupe_preserve_order(ensure_list(candidate_frontmatter.get("tags"))),
        "related_topics": dedupe_preserve_order(ensure_list(candidate_frontmatter.get("related_topics"))),
        "related_projects": dedupe_preserve_order(ensure_list(candidate_frontmatter.get("related_projects"))),
    }


def merge_reviewed_frontmatter(existing: Dict[str, Any], candidate: Dict[str, Any], reviewed_by: str) -> Dict[str, Any]:
    merged = dict(existing)
    merged["payload_schema_version"] = candidate.get("payload_schema_version", PAYLOAD_SCHEMA_VERSION)
    merged["review_status"] = "approved"
    merged["promotion_status"] = "reviewed"
    merged["synced_on"] = today_iso()
    merged["reviewed_by"] = reviewed_by
    merged["reviewed_key"] = candidate["reviewed_key"]
    merged["index_targets"] = dedupe_preserve_order(ensure_list(existing.get("index_targets")) + ensure_list(candidate.get("index_targets")))
    merged["tags"] = dedupe_preserve_order(ensure_list(existing.get("tags")) + ensure_list(candidate.get("tags")))
    merged["related_topics"] = dedupe_preserve_order(ensure_list(existing.get("related_topics")) + ensure_list(candidate.get("related_topics")))
    merged["related_projects"] = dedupe_preserve_order(ensure_list(existing.get("related_projects")) + ensure_list(candidate.get("related_projects")))
    return merged


def merge_reviewed_body(existing_body: str, candidate_body: str) -> str:
    cleaned_existing = existing_body.rstrip()
    cleaned_candidate = candidate_body.rstrip()
    if cleaned_candidate in cleaned_existing:
        return cleaned_existing + "\n"
    marker = "## Promotion Updates"
    addition = f"- {now_iso()}: merged candidate update\n"
    if marker not in cleaned_existing:
        return f"{cleaned_existing}\n\n{marker}\n\n{addition}"
    return f"{cleaned_existing}\n{addition}"


def promote_candidate(vault_root: Path, candidate_file: Path, reviewed_by: str = DEFAULT_REVIEWED_BY, repo_root: Path | None = None) -> Dict[str, Any]:
    repo_root = repo_root or REPO_ROOT
    ensure_workflow_template_repo(repo_root)

    candidate_path = candidate_file if candidate_file.is_absolute() else repo_root / candidate_file
    if not candidate_path.exists():
        raise FileNotFoundError(f"candidate file 不存在：{candidate_path}")

    frontmatter, body = parse_frontmatter(candidate_path.read_text(encoding="utf-8"))
    if frontmatter.get("note_kind") != "reviewed-sync-candidate":
        raise ValueError("candidate file 必須是 reviewed-sync-candidate")

    target_reviewed_dir = normalize_target_reviewed_dir(str(frontmatter.get("target_reviewed_dir", "")))
    reviewed_root = vault_root / REVIEWED_REL
    target_dir = reviewed_root / target_reviewed_dir
    target_dir.mkdir(parents=True, exist_ok=True)

    reviewed_key = str(frontmatter.get("reviewed_key") or build_reviewed_key(frontmatter))
    matches = find_note_by_key(reviewed_root, "reviewed_key", reviewed_key)
    updated_indexes: List[str] = []

    if matches:
        chosen = matches[0]
        merged_frontmatter = merge_reviewed_frontmatter(chosen["frontmatter"], frontmatter, reviewed_by)
        merged_body = merge_reviewed_body(chosen["body"], body)
        chosen["path"].write_text(
            f"{render_frontmatter(merged_frontmatter)}\n\n{merged_body.rstrip()}\n",
            encoding="utf-8",
        )
        archived = archive_candidate(candidate_path, vault_root)
        for target in ensure_list(merged_frontmatter.get("index_targets")):
            index_path = vault_root / INDEXES_REL / normalize_index_target(target)
            if update_index_file(index_path, chosen["path"], vault_root, merged_frontmatter["title"]):
                updated_indexes.append(str(index_path))
        return {
            "status": "ok",
            "action": "merge",
            "target_note": str(chosen["path"]),
            "archived_candidate": str(archived),
            "updated_indexes": updated_indexes,
            "reviewed_key": reviewed_key,
        }

    filename = build_reviewed_filename(frontmatter, target_dir)
    target_path = target_dir / filename
    reviewed_frontmatter = build_reviewed_frontmatter(frontmatter, reviewed_by)
    candidate_path.replace(target_path)
    target_path.write_text(
        f"{render_frontmatter(reviewed_frontmatter)}\n\n{body.rstrip()}\n",
        encoding="utf-8",
    )

    for target in ensure_list(reviewed_frontmatter.get("index_targets")):
        index_path = vault_root / INDEXES_REL / normalize_index_target(target)
        if update_index_file(index_path, target_path, vault_root, reviewed_frontmatter["title"]):
            updated_indexes.append(str(index_path))

    return {
        "status": "ok",
        "action": "promote",
        "target_note": str(target_path),
        "archived_candidate": None,
        "updated_indexes": updated_indexes,
        "reviewed_key": reviewed_key,
    }


def handle_write_candidate(args: argparse.Namespace) -> Dict[str, Any]:
    repo_root = REPO_ROOT
    vault_root = resolve_vault_root(args.vault_root, repo_root)

    if args.payload_file or args.payload_stdin:
        payload = load_json_payload(args.payload_file, use_stdin=args.payload_stdin)
        validate_json_payload_contract(payload)
    elif args.source_file:
        payload = build_payload_from_source_file(args, repo_root)
    else:
        payload = build_payload_from_summary(args)

    return write_candidate(vault_root, payload, repo_root=repo_root)


def handle_promote_candidate(args: argparse.Namespace) -> Dict[str, Any]:
    repo_root = REPO_ROOT
    vault_root = resolve_vault_root(args.vault_root, repo_root)
    return promote_candidate(vault_root, Path(args.candidate_file), reviewed_by=args.reviewed_by, repo_root=repo_root)


def parse_args(argv: List[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Manage reviewed-sync candidate writing and promotion in workflow template repo.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    write_parser = subparsers.add_parser("write-candidate", help="Write or update a reviewed-sync candidate note")
    write_parser.add_argument("--vault-root", help="Obsidian vault root; defaults to OBSIDIAN_VAULT_ROOT")
    input_group = write_parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument("--payload-file", help="Structured JSON payload file")
    input_group.add_argument("--payload-stdin", action="store_true", help="Read structured JSON payload from stdin")
    input_group.add_argument("--source-file", help="Source file inside the workflow template repo")
    input_group.add_argument("--summary-file", help="Manual summary text file")
    input_group.add_argument("--summary-text", help="Manual summary text")
    write_parser.add_argument("--title", help="Candidate title")
    write_parser.add_argument("--source-repo", default=DEFAULT_SOURCE_REPO)
    write_parser.add_argument("--source-type", help="Source type, e.g. repo-file / manual-summary / maintainer-policy")
    write_parser.add_argument("--source-path", help="Optional logical source path for manual summary mode")
    write_parser.add_argument("--target-reviewed-dir", help="Relative target dir under 20-reviewed")
    write_parser.add_argument("--index-target", action="append", default=[], help="Relative file under 00-indexes, repeatable")
    write_parser.add_argument("--tag", action="append", default=[])
    write_parser.add_argument("--related-topic", action="append", default=[])
    write_parser.add_argument("--related-project", action="append", default=[])
    write_parser.add_argument("--why-in-inbox", action="append", default=[])
    write_parser.add_argument("--reusability-check", action="append", default=[])
    write_parser.add_argument("--next-review-action", action="append", default=[])
    write_parser.add_argument("--source-note", action="append", default=[])
    write_parser.add_argument("--source-excerpt-max-lines", type=int, default=40)

    promote_parser = subparsers.add_parser("promote-candidate", help="Promote a reviewed-sync candidate into 20-reviewed")
    promote_parser.add_argument("--vault-root", help="Obsidian vault root; defaults to OBSIDIAN_VAULT_ROOT")
    promote_parser.add_argument("--candidate-file", required=True, help="Candidate markdown path")
    promote_parser.add_argument("--reviewed-by", default=DEFAULT_REVIEWED_BY)

    return parser.parse_args(argv)


def main(argv: List[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        if args.command == "write-candidate":
            result = handle_write_candidate(args)
        else:
            result = handle_promote_candidate(args)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except Exception as exc:
        print(
            json.dumps(
                {
                    "status": "error",
                    "action": args.command,
                    "reason": str(exc),
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 1


__all__ = [
    "ARCHIVE_REL",
    "CANDIDATES_REL",
    "DEFAULT_SOURCE_REPO",
    "PAYLOAD_SCHEMA_VERSION",
    "INDEXES_REL",
    "REPO_ROOT",
    "REVIEWED_REL",
    "archive_candidate",
    "build_candidate_body",
    "build_candidate_frontmatter",
    "build_candidate_key",
    "build_payload_from_source_file",
    "build_payload_from_summary",
    "build_reviewed_filename",
    "build_reviewed_frontmatter",
    "build_reviewed_key",
    "create_index_file",
    "default_index_targets",
    "ensure_workflow_template_repo",
    "find_note_by_key",
    "is_workflow_template_repo",
    "merge_candidate_frontmatter",
    "merge_reviewed_frontmatter",
    "normalize_candidate_payload",
    "parse_frontmatter",
    "promote_candidate",
    "render_frontmatter",
    "resolve_vault_root",
    "update_index_file",
    "validate_json_payload_contract",
    "write_candidate",
]


if __name__ == "__main__":
    raise SystemExit(main())
