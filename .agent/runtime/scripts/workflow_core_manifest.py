#!/usr/bin/env python3
"""Shared helpers for reading and querying workflow-core manifest contracts."""

from __future__ import annotations

import fnmatch
from pathlib import Path
from typing import Any


def normalize_path(value: str) -> str:
    path = str(value or "").strip()
    if path.startswith("./"):
        return path[2:]
    return path


def manifest_default_path(repo_root: Path) -> Path:
    return repo_root / "core_ownership_manifest.yml"


def parse_scalar(value: str) -> Any:
    raw = value.strip()
    if not raw:
        return ""
    if raw[0] == raw[-1] and raw[0] in {'"', "'"}:
        return raw[1:-1]
    lowered = raw.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    if lowered in {"null", "none"}:
        return None
    try:
        return int(raw)
    except ValueError:
        pass
    try:
        return float(raw)
    except ValueError:
        pass
    return raw


def tokenize_yaml(text: str) -> list[tuple[int, str]]:
    tokens: list[tuple[int, str]] = []
    for raw_line in text.splitlines():
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        indent = len(raw_line) - len(raw_line.lstrip(" "))
        tokens.append((indent, stripped))
    return tokens


def parse_yaml_block(tokens: list[tuple[int, str]], index: int, indent: int) -> tuple[Any, int]:
    if index >= len(tokens):
        return {}, index
    if tokens[index][1].startswith("- "):
        return parse_yaml_sequence(tokens, index, indent)
    return parse_yaml_mapping(tokens, index, indent)


def parse_yaml_mapping(tokens: list[tuple[int, str]], index: int, indent: int) -> tuple[dict[str, Any], int]:
    mapping: dict[str, Any] = {}
    while index < len(tokens):
        token_indent, text = tokens[index]
        if token_indent != indent or text.startswith("- "):
            break
        if ":" not in text:
            raise ValueError(f"Invalid mapping entry: {text}")
        key, rest = text.split(":", 1)
        key = key.strip()
        rest = rest.lstrip()
        index += 1
        if rest:
            mapping[key] = parse_scalar(rest)
            continue
        if index < len(tokens) and tokens[index][0] > indent:
            value, index = parse_yaml_block(tokens, index, tokens[index][0])
        else:
            value = {}
        mapping[key] = value
    return mapping, index


def parse_yaml_sequence(tokens: list[tuple[int, str]], index: int, indent: int) -> tuple[list[Any], int]:
    sequence: list[Any] = []
    while index < len(tokens):
        token_indent, text = tokens[index]
        if token_indent != indent or not text.startswith("- "):
            break
        item_text = text[2:].strip()
        index += 1
        if not item_text:
            if index < len(tokens) and tokens[index][0] > indent:
                item, index = parse_yaml_block(tokens, index, tokens[index][0])
            else:
                item = None
            sequence.append(item)
            continue
        if ":" in item_text:
            key, rest = item_text.split(":", 1)
            item: dict[str, Any] = {}
            key = key.strip()
            rest = rest.lstrip()
            if rest:
                item[key] = parse_scalar(rest)
            else:
                if index < len(tokens) and tokens[index][0] > indent:
                    value, index = parse_yaml_block(tokens, index, tokens[index][0])
                else:
                    value = {}
                item[key] = value
            if index < len(tokens) and tokens[index][0] > indent:
                extra, index = parse_yaml_block(tokens, index, tokens[index][0])
                if not isinstance(extra, dict):
                    raise ValueError(f"Expected mapping continuation for sequence item: {item_text}")
                item.update(extra)
            sequence.append(item)
            continue
        sequence.append(parse_scalar(item_text))
    return sequence, index


def load_manifest(manifest_path: Path) -> dict[str, Any]:
    if not manifest_path.exists():
        raise FileNotFoundError(f"manifest not found: {manifest_path}")
    tokens = tokenize_yaml(manifest_path.read_text(encoding="utf-8"))
    if not tokens:
        raise ValueError(f"manifest is empty: {manifest_path}")
    parsed, index = parse_yaml_block(tokens, 0, tokens[0][0])
    if index != len(tokens):
        raise ValueError(f"manifest parse did not consume all tokens: {manifest_path}")
    if not isinstance(parsed, dict):
        raise ValueError(f"manifest root must be a mapping: {manifest_path}")
    return parsed


def unique_paths(values: list[str]) -> list[str]:
    output: list[str] = []
    for item in values:
        normalized = normalize_path(item)
        if normalized and normalized not in output:
            output.append(normalized)
    return output


def path_matches_pattern(path: str, pattern: str) -> bool:
    normalized_path = normalize_path(path)
    normalized_pattern = normalize_path(pattern)
    if not normalized_pattern:
        return False
    if normalized_pattern.endswith("/**") and not any(char in normalized_pattern[:-3] for char in "*?["):
        return normalized_path.startswith(normalized_pattern[:-3])
    if any(char in normalized_pattern for char in "*?["):
        return fnmatch.fnmatchcase(normalized_path, normalized_pattern)
    return normalized_path == normalized_pattern or normalized_path.startswith(normalized_pattern + "/")


def pattern_anchor(pattern: str) -> str:
    normalized = normalize_path(pattern)
    if normalized.endswith("/**"):
        return normalized[:-3].rstrip("/")
    wildcard_positions = [normalized.find(char) for char in "*?[" if char in normalized]
    if wildcard_positions:
        position = min(pos for pos in wildcard_positions if pos >= 0)
        return normalized[:position].rstrip("/")
    return normalized


def split_compound_targets(value: str) -> list[str]:
    return [normalize_path(part) for part in str(value or "").split("+") if normalize_path(part)]


def get_required_live_paths(manifest: dict[str, Any]) -> list[str]:
    contract = manifest.get("root_path_contract", {})
    values = contract.get("required_live_paths", [])
    return unique_paths([str(item) for item in values])


def get_managed_patterns(manifest: dict[str, Any]) -> list[str]:
    managed = manifest.get("managed_paths", [])
    return unique_paths([str(item.get("path", "")) for item in managed if isinstance(item, dict)])


def get_overlay_patterns(manifest: dict[str, Any]) -> list[str]:
    excluded = manifest.get("excluded_paths", [])
    return unique_paths([str(item.get("path", "")) for item in excluded if isinstance(item, dict)])


def get_state_patterns(manifest: dict[str, Any]) -> list[str]:
    patterns: list[str] = []
    for item in manifest.get("split_required", []):
        if isinstance(item, dict):
            patterns.extend(split_compound_targets(str(item.get("recommended_target", ""))))

    skill_ownership = manifest.get("skill_ownership", {})
    local_target = skill_ownership.get("local_install_target")
    if local_target:
        patterns.extend(split_compound_targets(str(local_target)))

    for item in manifest.get("excluded_paths", []):
        if not isinstance(item, dict):
            continue
        category = str(item.get("category", "")).strip()
        path = str(item.get("path", "")).strip()
        if category == "environment-local":
            patterns.append(path)
        if path.startswith(".service/") or path.startswith(".agent/state/") or path.startswith(".agent/config/"):
            patterns.append(path)
        if "__pycache__" in path:
            patterns.append(path)
    return unique_paths(patterns)


def get_projection_artifact_path(manifest: dict[str, Any]) -> str:
    section = manifest.get("projection_bootstrap", {})
    return normalize_path(str(section.get("artifact_path", "")))


def get_smoke_suite_path(manifest: dict[str, Any]) -> str:
    section = manifest.get("verification_strategy", {})
    return normalize_path(str(section.get("portable_smoke_suite_path", "")))


def get_canonical_manifest_path(manifest: dict[str, Any]) -> str:
    section = manifest.get("automation_contract", {})
    return normalize_path(str(section.get("canonical_manifest_path", "")))


def get_export_profiles(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    values = manifest.get("export_profiles", [])
    return [item for item in values if isinstance(item, dict)]


def get_default_export_profile_name(manifest: dict[str, Any]) -> str:
    for profile in get_export_profiles(manifest):
        name = str(profile.get("name", "")).strip()
        status = str(profile.get("status", "")).strip().lower()
        if name and status == "active":
            return name
    return ""


def get_export_profile(manifest: dict[str, Any], profile_name: str) -> dict[str, Any]:
    requested_name = str(profile_name or "").strip()
    if not requested_name:
        raise KeyError("export profile name is required")

    for profile in get_export_profiles(manifest):
        if str(profile.get("name", "")).strip() != requested_name:
            continue
        includes = unique_paths([str(item) for item in profile.get("includes", [])])
        excludes = unique_paths([str(item) for item in profile.get("excludes", [])])
        deferred_paths = [item for item in profile.get("deferred_paths", []) if isinstance(item, dict)]
        notes = [str(item) for item in profile.get("notes", [])]
        return {
            "name": requested_name,
            "status": str(profile.get("status", "")).strip().lower(),
            "purpose": str(profile.get("purpose", "")).strip(),
            "includes": includes,
            "excludes": excludes,
            "deferred_paths": deferred_paths,
            "notes": notes,
        }

    raise KeyError(f"export profile not found: {requested_name}")
