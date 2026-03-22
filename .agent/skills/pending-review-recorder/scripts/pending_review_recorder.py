# -*- coding: utf-8 -*-
"""
.agent/skills/pending-review-recorder/scripts/pending_review_recorder.py
====================================================================
用途：將 triage 類工作事件寫入 pending-review-notes，並處理 dedupe / update
職責：
  - 驗證事件 payload 是否可記錄
  - 依 dedupe key 搜尋既有 note
  - 建立新 note 或更新既有 note
  - 套用穩定檔名規則與搜尋更新流程
====================================================================

使用方式：
    python .agent/skills/pending-review-recorder/scripts/pending_review_recorder.py \
      --notes-dir /path/to/pending-review-notes \
      --payload-file /path/to/event.json

若未提供 --payload-file，則會從 stdin 讀取 JSON payload。
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple


SKILLS_ROOT = Path(__file__).resolve().parents[2]

ALLOWED_EVENT_CLASSES = {
    "blocker",
    "qa-defect",
    "security-signal",
    "workaround",
    "user-requested-record",
}

REQUIRED_PAYLOAD_FIELDS = {
    "title",
    "source_repo",
    "project_scope",
    "recorded_by_role",
    "detection_mode",
    "event_class",
    "workflow_phase",
    "impact_level",
    "reproducibility",
    "module_area",
    "symptom_signature",
}

SEVERITY_ORDER = {
    "low": 1,
    "medium": 2,
    "high": 3,
    "critical": 4,
}


def validate_output_schema(result: Dict[str, Any], skill_name: str) -> Dict[str, Any]:
    try:
        import jsonschema
    except ImportError:
        return result

    schema_path = SKILLS_ROOT / "schemas" / f"{skill_name}_output.schema.json"
    if not schema_path.exists():
        return result

    try:
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        jsonschema.validate(result, schema)
        return result
    except Exception as exc:  # pragma: no cover - graceful degradation
        result.setdefault("validation_errors", []).append({"message": str(exc)})
        return result


def slugify(value: str, max_length: int = 80) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.strip().lower())
    slug = re.sub(r"-+", "-", slug).strip("-")
    if not slug:
        slug = "event"
    return slug[:max_length].rstrip("-")


def today_iso() -> str:
    return datetime.now(UTC).date().isoformat()


def now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


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
        if not line.strip():
            index += 1
            continue
        if ":" not in line:
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


def render_scalar(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


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


def build_dedupe_key(payload: Dict[str, Any]) -> str:
    return "|".join(
        [
            str(payload.get("project_scope", "")).strip(),
            str(payload.get("recorded_by_role", "")).strip(),
            str(payload.get("event_class", "")).strip(),
            str(payload.get("module_area", "")).strip(),
            str(payload.get("symptom_signature", "")).strip(),
        ]
    )


def build_filename(payload: Dict[str, Any], notes_dir: Path) -> str:
    occurred_on = str(payload.get("occurred_on") or today_iso())
    role = slugify(str(payload.get("recorded_by_role", "unknown")), max_length=24)
    event_class = slugify(str(payload.get("event_class", "event")), max_length=32)
    signature = slugify(str(payload.get("symptom_signature", "event")), max_length=72)
    base_name = f"{occurred_on}-{role}-{event_class}-{signature}"
    candidate = f"{base_name}.md"
    counter = 2
    while (notes_dir / candidate).exists():
        candidate = f"{base_name}-{counter}.md"
        counter += 1
    return candidate


def choose_higher_severity(left: str, right: str) -> str:
    left_rank = SEVERITY_ORDER.get(left, 0)
    right_rank = SEVERITY_ORDER.get(right, 0)
    return left if left_rank >= right_rank else right


def list_note_files(notes_dir: Path) -> List[Path]:
    if not notes_dir.exists():
        return []
    return sorted(path for path in notes_dir.rglob("*.md") if path.is_file())


def sort_key_for_match(note: Dict[str, Any]) -> Tuple[str, str]:
    frontmatter = note["frontmatter"]
    last_seen = str(frontmatter.get("last_seen_on") or frontmatter.get("occurred_on") or "")
    return (last_seen, str(note["path"]))


def find_matching_notes(notes_dir: Path, dedupe_key: str) -> List[Dict[str, Any]]:
    matches: List[Dict[str, Any]] = []
    for note_path in list_note_files(notes_dir):
        frontmatter, body = parse_frontmatter(note_path.read_text(encoding="utf-8"))
        if not frontmatter:
            continue
        if frontmatter.get("note_kind") != "pending-review-note":
            continue
        existing_key = build_dedupe_key(frontmatter)
        if existing_key == dedupe_key:
            matches.append({"path": note_path, "frontmatter": frontmatter, "body": body})
    return sorted(matches, key=sort_key_for_match, reverse=True)


def format_section_items(value: Any, fallback: str) -> str:
    items = ensure_list(value)
    if not items:
        items = [fallback]
    return "\n".join(f"- {item}" for item in items)


def build_body(payload: Dict[str, Any]) -> str:
    symptom_summary = str(payload.get("symptom_summary") or payload.get("title") or "待補症狀摘要")
    what_happened = format_section_items(payload.get("what_happened"), "待補發生情境")
    impact_summary = format_section_items(payload.get("impact_summary"), "待補影響範圍")
    evidence_summary = format_section_items(payload.get("evidence_summary") or payload.get("evidence_refs"), "待補 evidence reference")
    workaround_summary = format_section_items(payload.get("workaround_summary"), "尚未提供 workaround")
    next_action_summary = format_section_items(payload.get("next_action_summary"), "待補下一步")

    return (
        "# Symptom Summary\n\n"
        f"{symptom_summary}\n\n"
        "# What Happened\n\n"
        f"{what_happened}\n\n"
        "# Impact\n\n"
        f"{impact_summary}\n\n"
        "# Evidence Summary\n\n"
        f"{evidence_summary}\n\n"
        "# Workaround\n\n"
        f"{workaround_summary}\n\n"
        "# Next Action\n\n"
        f"{next_action_summary}\n"
    )


def append_update_history(existing_body: str, payload: Dict[str, Any]) -> str:
    summary = str(payload.get("symptom_summary") or payload.get("title") or "事件再次出現")
    entry = f"- {now_iso()}: {summary}"
    marker = "## Update History"
    body = existing_body.rstrip()
    if marker not in body:
        return f"{body}\n\n{marker}\n\n{entry}\n"
    prefix, suffix = body.split(marker, 1)
    suffix = suffix.rstrip()
    if suffix:
        return f"{prefix}{marker}{suffix}\n{entry}\n"
    return f"{prefix}{marker}\n\n{entry}\n"


def merge_frontmatter(existing: Dict[str, Any], payload: Dict[str, Any]) -> Dict[str, Any]:
    merged = dict(existing)
    merged["last_seen_on"] = str(payload.get("last_seen_on") or payload.get("occurred_on") or today_iso())
    merged["occurrence_count"] = int(existing.get("occurrence_count", 1) or 1) + int(payload.get("occurrence_increment", 1) or 1)
    merged["impact_level"] = choose_higher_severity(str(existing.get("impact_level", "low")), str(payload.get("impact_level", "low")))
    merged["current_status"] = str(payload.get("current_status") or existing.get("current_status") or "pending-triage")
    merged["workaround_applied"] = bool(existing.get("workaround_applied", False) or payload.get("workaround_applied", False))
    merged["next_owner"] = str(payload.get("next_owner") or existing.get("next_owner") or "engineer")
    merged["evidence_refs"] = dedupe_preserve_order(ensure_list(existing.get("evidence_refs")) + ensure_list(payload.get("evidence_refs")))
    merged["tags"] = dedupe_preserve_order(ensure_list(existing.get("tags")) + ensure_list(payload.get("tags")))
    return merged


def build_frontmatter(payload: Dict[str, Any]) -> Dict[str, Any]:
    occurred_on = str(payload.get("occurred_on") or today_iso())
    return {
        "title": str(payload["title"]),
        "note_kind": "pending-review-note",
        "source_repo": str(payload["source_repo"]),
        "project_scope": str(payload["project_scope"]),
        "recorded_by_role": str(payload["recorded_by_role"]),
        "detection_mode": str(payload["detection_mode"]),
        "event_class": str(payload["event_class"]),
        "workflow_phase": str(payload["workflow_phase"]),
        "current_status": str(payload.get("current_status") or "pending-triage"),
        "impact_level": str(payload["impact_level"]),
        "reproducibility": str(payload["reproducibility"]),
        "module_area": str(payload["module_area"]),
        "symptom_signature": str(payload["symptom_signature"]),
        "occurred_on": occurred_on,
        "last_seen_on": str(payload.get("last_seen_on") or occurred_on),
        "occurrence_count": int(payload.get("occurrence_count", 1) or 1),
        "evidence_refs": dedupe_preserve_order(ensure_list(payload.get("evidence_refs"))),
        "workaround_applied": bool(payload.get("workaround_applied", False)),
        "next_owner": str(payload.get("next_owner") or payload.get("recorded_by_role") or "engineer"),
        "tags": dedupe_preserve_order(ensure_list(payload.get("tags")) or ["pending-review", "triage"]),
    }


def validate_payload(payload: Dict[str, Any]) -> List[str]:
    errors = []
    missing = sorted(field for field in REQUIRED_PAYLOAD_FIELDS if not str(payload.get(field, "")).strip())
    if missing:
        errors.append(f"缺少必要欄位：{', '.join(missing)}")
    if payload.get("event_class") not in ALLOWED_EVENT_CLASSES:
        errors.append("event_class 不在 allow-list 中")
    return errors


def should_skip(payload: Dict[str, Any]) -> Tuple[bool, str]:
    if payload.get("contains_sensitive_data"):
        return True, "payload contains sensitive data"
    if payload.get("raw_output_only"):
        return True, "payload is raw-output-only"
    if payload.get("low_value_once"):
        return True, "payload is a low-value one-off event"
    if payload.get("formalized_knowledge"):
        return True, "payload already belongs to reviewed or decision knowledge"
    if payload.get("expected_in_progress_failure"):
        return True, "payload is an expected in-progress failure"
    if payload.get("auto_record_allowed") is False:
        return True, "caller marked event as not auto-recordable"
    return False, ""


def record_event(payload: Dict[str, Any], notes_dir: str | Path) -> Dict[str, Any]:
    notes_root = Path(notes_dir)
    errors = validate_payload(payload)
    if errors:
        return {
            "status": "error",
            "action": "skip",
            "reason": "; ".join(errors),
            "role": payload.get("recorded_by_role", "unknown"),
            "dedupe_key": build_dedupe_key(payload),
            "target_note": None,
        }

    should_skip_event, skip_reason = should_skip(payload)
    if should_skip_event:
        return {
            "status": "ok",
            "action": "skip",
            "reason": skip_reason,
            "role": payload["recorded_by_role"],
            "dedupe_key": build_dedupe_key(payload),
            "target_note": None,
        }

    notes_root.mkdir(parents=True, exist_ok=True)
    dedupe_key = build_dedupe_key(payload)
    matches = find_matching_notes(notes_root, dedupe_key)
    duplicate_candidates = [str(item["path"]) for item in matches[1:]]

    if matches:
        chosen = matches[0]
        merged_frontmatter = merge_frontmatter(chosen["frontmatter"], payload)
        updated_body = append_update_history(chosen["body"], payload)
        chosen["path"].write_text(
            f"{render_frontmatter(merged_frontmatter)}\n\n{updated_body.rstrip()}\n",
            encoding="utf-8",
        )
        return {
            "status": "ok",
            "action": "update",
            "reason": "matched existing note by dedupe key",
            "role": payload["recorded_by_role"],
            "dedupe_key": dedupe_key,
            "target_note": str(chosen["path"]),
            "matched_notes": [str(item["path"]) for item in matches],
            "duplicate_note_candidates": duplicate_candidates,
            "filename_rule": "preserve existing filename on update",
            "search_strategy": "recursive markdown scan + frontmatter dedupe key match",
        }

    frontmatter = build_frontmatter(payload)
    filename = build_filename(frontmatter, notes_root)
    note_path = notes_root / filename
    note_path.write_text(f"{render_frontmatter(frontmatter)}\n\n{build_body(payload).rstrip()}\n", encoding="utf-8")
    return {
        "status": "ok",
        "action": "create",
        "reason": "no existing note matched dedupe key",
        "role": payload["recorded_by_role"],
        "dedupe_key": dedupe_key,
        "target_note": str(note_path),
        "matched_notes": [],
        "duplicate_note_candidates": [],
        "filename_rule": "<occurred_on>-<recorded_by_role>-<event_class>-<symptom_signature>.md",
        "search_strategy": "recursive markdown scan + frontmatter dedupe key match",
    }


def load_payload(payload_file: str | None) -> Dict[str, Any]:
    if payload_file:
        return json.loads(Path(payload_file).read_text(encoding="utf-8"))
    return json.loads(sys.stdin.read())


def parse_args(argv: List[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Record or update a pending-review note with dedupe logic.")
    parser.add_argument("--notes-dir", required=True, help="Path to pending-review-notes directory")
    parser.add_argument("--payload-file", help="JSON file containing the event payload")
    return parser.parse_args(argv)


def main(argv: List[str] | None = None) -> int:
    args = parse_args(argv)
    payload = load_payload(args.payload_file)
    result = record_event(payload, args.notes_dir)
    result = validate_output_schema(result, "pending_review_recorder")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if result["status"] == "error" else 0


__all__ = [
    "ALLOWED_EVENT_CLASSES",
    "REQUIRED_PAYLOAD_FIELDS",
    "append_update_history",
    "build_body",
    "build_dedupe_key",
    "build_filename",
    "build_frontmatter",
    "choose_higher_severity",
    "dedupe_preserve_order",
    "find_matching_notes",
    "list_note_files",
    "main",
    "merge_frontmatter",
    "parse_frontmatter",
    "record_event",
    "render_frontmatter",
    "should_skip",
    "slugify",
    "validate_payload",
]


if __name__ == "__main__":
    raise SystemExit(main())
