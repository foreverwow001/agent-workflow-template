# -*- coding: utf-8 -*-
"""
.agent/skills/github-explorer/scripts/github_explorer.py
=====================================
用途：GitHub 技能搜尋與下載工具
職責：搜尋、預覽、下載、回滾外部技能，並使用 shared metadata 管理白名單與 manifest
=====================================
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from pathlib import PurePosixPath
from urllib.parse import urlparse


SKILLS_DIR = Path(__file__).resolve().parents[2]
if str(SKILLS_DIR) not in sys.path:
    sys.path.insert(0, str(SKILLS_DIR))

from _shared import (  # noqa: E402
    AGENT_DIR,
    AUDIT_LOG_PATH,
    iter_skill_package_dirs,
    iter_local_skill_package_dirs,
    LOCAL_INDEX_PATH,
    LOCAL_SKILLS_DIR,
    package_dir_to_skill_name,
    read_manifest,
    read_whitelist,
    skill_name_to_package_dir,
    write_manifest,
)


GITHUB_API_BASE = "https://api.github.com"
GITHUB_RAW_BASE = "https://raw.githubusercontent.com"
MAX_SEARCH_RESULTS = 10
PACKAGE_CONTAINER_DIRS = {"scripts", "resources", "assets", "docs", "examples", "prompts", "templates", "data"}
PACKAGE_TAXONOMY_DIRS = {"skills", ".curated", ".experimental", ".system", ".official", ".community"}
GENERIC_EXTERNAL_NAMES = {
    "skill",
    "readme",
    "index",
    "main",
    "__init__",
    "scripts",
    "resources",
    "assets",
    "docs",
    "examples",
    "prompts",
    "templates",
    "data",
}


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


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def write_audit_log(action: str, skill_name: str, **kwargs: Any) -> None:
    extra = " ".join(f"{key}={value}" for key, value in kwargs.items())
    log_line = f"[{_now_iso()}] ACTION={action} SKILL={skill_name} {extra}\n"
    try:
        AUDIT_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(AUDIT_LOG_PATH, "a", encoding="utf-8") as handle:
            handle.write(log_line)
    except Exception:
        pass


def _approved_sources(whitelist: Dict[str, Any]) -> List[str]:
    approved = whitelist.get("approved_sources")
    if isinstance(approved, list):
        return [str(item) for item in approved if str(item).strip()]
    legacy = whitelist.get("whitelist")
    if isinstance(legacy, list):
        return [str(item) for item in legacy if str(item).strip()]
    return []


def check_whitelist(repo_full_name: str) -> Dict[str, Any]:
    import fnmatch

    approved_sources = _approved_sources(read_whitelist())
    for pattern in approved_sources:
        if fnmatch.fnmatch(repo_full_name.lower(), pattern.lower()):
            return {"approved": True, "matched_pattern": pattern, "repo": repo_full_name}

    write_audit_log("whitelist_violation", repo_full_name, status="blocked")
    return {
        "approved": False,
        "repo": repo_full_name,
        "message": f"⛔ Repo '{repo_full_name}' 不在白名單中",
        "approved_patterns": approved_sources,
    }


def calculate_file_hash(file_path: str) -> str:
    try:
        with open(file_path, "rb") as handle:
            return hashlib.sha256(handle.read()).hexdigest()
    except Exception:
        return ""


def add_to_manifest(
    skill_name: str,
    source_repo: str,
    file_path: str,
    content_hash: str,
    package_path: str,
    commit_sha: str = "unknown",
) -> None:
    manifest = read_manifest()
    skills = manifest.get("skills", [])
    if not isinstance(skills, list):
        skills = []
    manifest["skills"] = [entry for entry in skills if entry.get("name") != skill_name]
    manifest["skills"].append(
        {
            "name": skill_name,
            "type": "external",
            "source_repo": source_repo,
            "package_path": package_path,
            "path": file_path,
            "file_path": file_path,
            "commit_sha": commit_sha,
            "sha256_hash": content_hash,
            "downloaded_at": _now_iso(),
        }
    )
    manifest["last_updated"] = _now_iso()
    write_manifest(manifest)
    write_audit_log("manifest_update", skill_name, repo=source_repo, hash=content_hash[:16])


def remove_from_manifest(skill_name: str) -> bool:
    manifest = read_manifest()
    skills = manifest.get("skills", [])
    if not isinstance(skills, list):
        skills = []
    filtered = [entry for entry in skills if entry.get("name") != skill_name]
    if len(filtered) == len(skills):
        return False
    manifest["skills"] = filtered
    manifest["last_updated"] = _now_iso()
    write_manifest(manifest)
    return True


def remove_from_index(skill_name: str) -> bool:
    if not LOCAL_INDEX_PATH.exists():
        return False

    content = LOCAL_INDEX_PATH.read_text(encoding="utf-8")
    updated = content
    table_row_pattern = re.compile(rf"^\| `{re.escape(skill_name)}` \|.*\n?", re.MULTILINE)
    updated = table_row_pattern.sub("", updated)
    detail_pattern = re.compile(
        rf"\n### \d+\. {re.escape(skill_name)} \(外部技能\)\n\n.*?(?=\n### \d+\. |\Z)",
        re.DOTALL,
    )
    updated = detail_pattern.sub("\n", updated)

    if updated == content:
        return False

    LOCAL_INDEX_PATH.write_text(updated.rstrip() + "\n", encoding="utf-8")
    return True


def _normalize_external_skill_name(repo_full_name: str, candidate_name: str) -> str:
    base_name = candidate_name.strip()
    if not base_name or base_name.lower() in GENERIC_EXTERNAL_NAMES:
        base_name = repo_full_name.split("/")[-1]
    normalized = re.sub(r"[^a-z0-9]+", "_", base_name.lower().replace("-", "_"))
    normalized = re.sub(r"_+", "_", normalized).strip("_") or "external_skill"
    return normalized


def _resolve_external_package_layout(repo_full_name: str, remote_file_path: str) -> Dict[str, str]:
    remote_path = PurePosixPath(remote_file_path.strip("/"))
    parts = [part for part in remote_path.parts if part not in {"", "."}]
    if any(part == ".." for part in parts):
        raise ValueError(f"不支援的遠端路徑：{remote_file_path}")

    if not parts:
        skill_name = _normalize_external_skill_name(repo_full_name, repo_full_name.split("/")[-1])
        package_dir_name = skill_name_to_package_dir(skill_name)
        return {
            "skill_name": skill_name,
            "package_dir_name": package_dir_name,
            "package_relative_path": "README.md",
        }

    container_index = next(
        (index for index, part in enumerate(parts[:-1]) if part.lower() in PACKAGE_CONTAINER_DIRS and index > 0),
        None,
    )
    root_index = container_index - 1 if container_index is not None else max(len(parts) - 2, 0)

    while root_index > 0 and parts[root_index].lower() in PACKAGE_TAXONOMY_DIRS:
        root_index -= 1

    candidate_name = parts[root_index] if parts else repo_full_name.split("/")[-1]
    skill_name = _normalize_external_skill_name(repo_full_name, candidate_name)
    package_dir_name = skill_name_to_package_dir(skill_name)

    relative_parts = parts[root_index + 1 :] if root_index + 1 < len(parts) else [parts[-1]]
    if not relative_parts:
        relative_parts = [parts[-1]]

    file_name = relative_parts[-1]
    if file_name.lower() == "skill.md":
        relative_parts = ["SKILL.md"]
    elif file_name.lower() == "readme.md":
        relative_parts = ["README.md"]

    package_relative_path = PurePosixPath(*relative_parts).as_posix()
    return {
        "skill_name": skill_name,
        "package_dir_name": package_dir_name,
        "package_relative_path": package_relative_path,
    }


def _resolve_external_destination(repo_full_name: str, remote_file_path: str) -> tuple[str, Path, PurePosixPath]:
    layout = _resolve_external_package_layout(repo_full_name, remote_file_path)
    package_dir = LOCAL_SKILLS_DIR / layout["package_dir_name"]
    package_relative_path = PurePosixPath(layout["package_relative_path"])
    return layout["skill_name"], package_dir / package_relative_path, package_relative_path


def _to_agent_relative(path: Path) -> str:
    if path.is_absolute() and path.is_relative_to(AGENT_DIR):
        return f".agent/{path.relative_to(AGENT_DIR).as_posix()}"
    return str(path)


def _load_skill_converter_module():
    script_path = SKILLS_DIR / "skill-converter" / "scripts" / "skill_converter.py"
    spec = importlib.util.spec_from_file_location("skill_converter_impl", script_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"無法載入 skill_converter canonical script: {script_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def rollback_skill(skill_name: str) -> Dict[str, Any]:
    actions_taken: List[str] = []
    manifest = read_manifest()
    skills = manifest.get("skills", []) if isinstance(manifest.get("skills"), list) else []
    record = next((entry for entry in skills if entry.get("name") == skill_name), None)

    package_dir = LOCAL_SKILLS_DIR / skill_name_to_package_dir(skill_name)
    if record and isinstance(record.get("package_path"), str):
        package_path_value = record["package_path"]
        if package_path_value.startswith(".agent/skills_local/"):
            package_dir = LOCAL_SKILLS_DIR / package_path_value.replace(".agent/skills_local/", "", 1)
        elif package_path_value.startswith(".agent/skills/"):
            package_dir = SKILLS_DIR / package_path_value.replace(".agent/skills/", "", 1)
        else:
            candidate_package_dir = Path(package_path_value)
            if candidate_package_dir.is_absolute():
                package_dir = candidate_package_dir
    elif record and isinstance(record.get("file_path"), str):
        candidate = Path(record["file_path"])
        if candidate.is_absolute():
            if candidate.parent.name in PACKAGE_CONTAINER_DIRS:
                package_dir = candidate.parents[1]
            else:
                package_dir = candidate.parent
        elif record["file_path"].startswith(".agent/skills_local/"):
            relative_path = record["file_path"].replace(".agent/skills_local/", "", 1)
            resolved = LOCAL_SKILLS_DIR / relative_path
            if resolved.parent.name in PACKAGE_CONTAINER_DIRS:
                package_dir = resolved.parents[1]
            else:
                package_dir = resolved.parent
        elif record["file_path"].startswith(".agent/skills/"):
            relative_path = record["file_path"].replace(".agent/skills/", "", 1)
            resolved = SKILLS_DIR / relative_path
            if resolved.parent.name in PACKAGE_CONTAINER_DIRS:
                package_dir = resolved.parents[1]
            else:
                package_dir = resolved.parent

    if package_dir.exists():
        try:
            for child in sorted(package_dir.rglob("*"), reverse=True):
                if child.is_file() or child.is_symlink():
                    child.unlink()
                elif child.is_dir():
                    child.rmdir()
            package_dir.rmdir()
            actions_taken.append(f"已刪除 package：{package_dir.name}")
        except Exception as exc:
            actions_taken.append(f"刪除 package 失敗：{exc}")
    else:
        actions_taken.append(f"package 不存在：{package_dir.name}")

    if remove_from_manifest(skill_name):
        actions_taken.append("已從 manifest 移除")
    else:
        actions_taken.append("manifest 中無此技能記錄")

    if remove_from_index(skill_name):
        actions_taken.append("已從 INDEX.local.md 移除")
    else:
        actions_taken.append("INDEX.local.md 中無此技能記錄")

    write_audit_log("rollback", skill_name, status="success")
    return {
        "status": "success",
        "skill_name": skill_name,
        "actions_taken": actions_taken,
        "message": f"✅ 已成功回滾技能：{skill_name}",
    }


def _require_requests() -> tuple[Any, Any]:
    try:
        import requests
    except ImportError as exc:
        raise RuntimeError("缺少 requests 套件") from exc
    return requests, requests.exceptions


def _parse_repo_full_name(repo_url: str) -> str:
    if repo_url.startswith("http"):
        parsed = urlparse(repo_url)
        path_parts = parsed.path.strip("/").split("/")
        if len(path_parts) >= 2:
            return f"{path_parts[0]}/{path_parts[1]}"
        raise ValueError(f"無法解析 Repo URL：{repo_url}")
    return repo_url


def search_github_skills(keyword: str) -> Dict[str, Any]:
    try:
        requests, request_exceptions = _require_requests()
    except RuntimeError:
        return {
            "status": "error",
            "message": "缺少 requests 套件，無法執行 GitHub 搜尋",
            "suggestion": "請先安裝 requests，例如：pip install requests",
                "usage": "python .agent/skills/github-explorer/scripts/github_explorer.py search <keyword>",
        }

    query = f"{keyword} filename:SKILL.md"
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "IvyHouse-SkillExplorer/1.0",
    }
    token = os.getenv("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"token {token}"

    try:
        response = requests.get(
            f"{GITHUB_API_BASE}/search/code",
            params={"q": query, "per_page": MAX_SEARCH_RESULTS},
            headers=headers,
            timeout=30,
        )
        if response.status_code == 401:
            return {
                "status": "error",
                "message": "GitHub API 認證失敗 (401)，請檢查 GITHUB_TOKEN 是否正確",
                "auth_error": True,
            }
        if response.status_code == 403:
            return {
                "status": "error",
                "message": "GitHub API 請求次數已達上限（每小時 10 次），請稍後再試",
                "rate_limit": True,
            }
        if response.status_code != 200:
            return {
                "status": "error",
                "message": f"GitHub API 錯誤：{response.status_code}",
                "details": response.text[:500],
            }

        payload = response.json()
        seen_repos = set()
        results = []
        for item in payload.get("items", []):
            repository = item.get("repository", {})
            repo_full_name = repository.get("full_name", "")
            if not repo_full_name or repo_full_name in seen_repos:
                continue
            seen_repos.add(repo_full_name)
            results.append(
                {
                    "repo_name": repo_full_name,
                    "description": repository.get("description", "（無描述）") or "（無描述）",
                    "repo_url": repository.get("html_url", ""),
                    "skill_path": item.get("path", "SKILL.md"),
                    "stars": repository.get("stargazers_count", 0),
                }
            )

        return {
            "status": "success",
            "keyword": keyword,
            "total_count": payload.get("total_count", 0),
            "results": results,
            "message": f"找到 {len(results)} 個含有 SKILL.md 的 Repo",
        }
    except request_exceptions.Timeout:
        return {"status": "error", "message": "GitHub API 請求超時，請檢查網路連線"}
    except Exception as exc:
        return {"status": "error", "message": f"搜尋失敗：{exc}"}


def preview_skill(repo_url: str, skill_path: str = "SKILL.md") -> Dict[str, Any]:
    try:
        requests, _ = _require_requests()
    except RuntimeError:
        return {
            "status": "error",
            "message": "缺少 requests 套件，無法執行 GitHub 預覽",
            "suggestion": "請先安裝 requests，例如：pip install requests",
            "usage": "python .agent/skills/github-explorer/scripts/github_explorer.py preview <repo_url> [skill_path]",
        }

    try:
        repo_full_name = _parse_repo_full_name(repo_url)
    except ValueError as exc:
        return {"status": "error", "message": str(exc)}

    for branch in ["main", "master"]:
        raw_url = f"{GITHUB_RAW_BASE}/{repo_full_name}/{branch}/{skill_path}"
        try:
            response = requests.get(raw_url, timeout=15)
            if response.status_code == 200:
                content = response.text
                return {
                    "status": "success",
                    "repo": repo_full_name,
                    "skill_path": skill_path,
                    "branch": branch,
                    "content": content,
                    "content_length": len(content),
                    "message": "⚠️ 請審核以上內容。若確認安全，請使用 download 指令下載。",
                    "next_step": f"python .agent/skills/github-explorer/scripts/github_explorer.py download {repo_full_name} {skill_path} --confirm",
                }
        except Exception:
            continue

    return {
        "status": "error",
        "message": f"無法讀取 {repo_full_name} 的 {skill_path}，請確認檔案存在",
    }


def run_security_scan(file_path: str) -> Dict[str, Any]:
    reviewer_path = SKILLS_DIR / "code-reviewer" / "scripts" / "code_reviewer.py"
    if not reviewer_path.exists():
        return {"status": "warning", "message": "code_reviewer.py 不存在，跳過安全掃描"}

    try:
        result = subprocess.run(
            [sys.executable, str(reviewer_path), file_path],
            capture_output=True,
            text=True,
            timeout=30,
        )
        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError:
            return {
                "status": "warning",
                "message": "無法解析安全掃描結果",
                "raw_output": result.stdout[:500],
            }
    except subprocess.TimeoutExpired:
        return {"status": "error", "message": "安全掃描超時"}
    except Exception as exc:
        return {"status": "error", "message": f"安全掃描失敗：{exc}"}


def run_conversion_pipeline(
    file_path: str,
    skill_name: str,
    source_repo: str,
    package_relative_path: Optional[str] = None,
    user_confirmed: bool = False,
) -> Dict[str, Any]:
    try:
        skill_converter = _load_skill_converter_module()
        return skill_converter.convert_skill(
            file_path=file_path,
            skill_name=skill_name,
            source_repo=source_repo,
            package_relative_path=package_relative_path,
            user_confirmed=user_confirmed,
        )
    except Exception as exc:
        return {
            "status": "warning",
            "message": f"skill_converter 載入失敗，跳過進階轉換：{exc}",
        }


def download_skill(repo_url: str, file_path: str, target_dir: Optional[str] = None, user_confirmed: bool = False) -> Dict[str, Any]:
    if not user_confirmed:
        return {
            "status": "blocked",
            "message": "⛔ 安全機制啟動：下載前必須先執行 preview 並取得使用者確認",
            "action_required": "請先使用 preview 指令查看內容，確認無安全疑慮後再下載",
        }

    try:
        requests, _ = _require_requests()
    except RuntimeError:
        return {
            "status": "error",
            "message": "缺少 requests 套件，無法執行 GitHub 下載",
            "suggestion": "請先安裝 requests，例如：pip install requests",
            "usage": "python .agent/skills/github-explorer/scripts/github_explorer.py download <repo_url> <file_path> --confirm",
        }

    try:
        repo_full_name = _parse_repo_full_name(repo_url)
    except ValueError as exc:
        return {"status": "error", "message": str(exc)}

    whitelist_result = check_whitelist(repo_full_name)
    if not whitelist_result.get("approved"):
        return {
            "status": "blocked",
            "message": whitelist_result.get("message", "白名單檢查失敗"),
            "whitelist_check": whitelist_result,
            "action_required": "請聯繫 QA Team 將此 Repo 加入白名單",
        }

    write_audit_log("download_start", Path(file_path).stem, repo=repo_full_name)
    explicit_target_dir = Path(target_dir) if target_dir else None

    for branch in ["main", "master"]:
        raw_url = f"{GITHUB_RAW_BASE}/{repo_full_name}/{branch}/{file_path}"
        try:
            response = requests.get(raw_url, timeout=15)
            if response.status_code != 200:
                continue

            content = response.text
            skill_name, resolved_dest_path, package_relative_path = _resolve_external_destination(repo_full_name, file_path)
            if explicit_target_dir:
                dest_path = explicit_target_dir / skill_name_to_package_dir(skill_name) / package_relative_path
            else:
                dest_path = resolved_dest_path
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            dest_path.write_text(content, encoding="utf-8")

            scan_result = run_security_scan(str(dest_path))
            write_audit_log("security_scan", dest_path.stem, result=scan_result.get("status", "unknown"))
            if scan_result.get("status") == "fail":
                dest_path.unlink(missing_ok=True)
                write_audit_log("download_blocked", dest_path.stem, reason="security_scan_failed")
                return {
                    "status": "blocked",
                    "message": "🚨 安全掃描失敗！已自動刪除下載的檔案",
                    "scan_result": scan_result,
                    "deleted_file": str(dest_path),
                }

            content_hash = calculate_file_hash(str(dest_path))
            relative_dest = _to_agent_relative(dest_path)
            package_relative_root = dest_path.parents[len(package_relative_path.parts) - 1] if len(package_relative_path.parts) > 1 else dest_path.parent
            relative_package_root = _to_agent_relative(package_relative_root)
            add_to_manifest(skill_name, repo_full_name, relative_dest, content_hash, relative_package_root)
            write_audit_log("install", skill_name, repo=repo_full_name, hash=content_hash[:16])

            convert_result = run_conversion_pipeline(
                str(dest_path),
                skill_name,
                repo_full_name,
                package_relative_path=package_relative_path.as_posix(),
                user_confirmed=True,
            )
            return {
                "status": "success",
                "message": "✅ 成功下載、通過安全掃描並完成轉換",
                "source": raw_url,
                "destination": str(dest_path),
                "content_hash": content_hash,
                "scan_result": scan_result,
                "conversion_result": convert_result,
            }
        except Exception:
            continue

    return {"status": "error", "message": f"無法下載 {repo_full_name}/{file_path}"}


def list_local_skills() -> Dict[str, Any]:
    skills = []

    def collect(package_dirs, scope: str) -> None:
        for package_dir in package_dirs:
            skill_name = package_dir_to_skill_name(package_dir.name)
            try:
                entry_doc = package_dir / "SKILL.md"
                if not entry_doc.exists():
                    entry_doc = package_dir / "README.md"
                description = "（無描述）"
                if entry_doc.exists():
                    content = entry_doc.read_text(encoding="utf-8")
                    lines = content.splitlines()
                    if lines[:1] == ["---"]:
                        frontmatter_end = 1
                        while frontmatter_end < len(lines) and lines[frontmatter_end].strip() != "---":
                            frontmatter_end += 1
                        frontmatter = lines[1:frontmatter_end]
                        for line in frontmatter:
                            stripped = line.strip()
                            if stripped.startswith("description:"):
                                description = stripped.split(":", 1)[1].strip().strip('"')[:100] or description
                                break
                        lines = lines[frontmatter_end + 1 :] if frontmatter_end < len(lines) else []

                    if description == "（無描述）":
                        for line in lines:
                            stripped = line.strip()
                            if stripped and not stripped.startswith("#"):
                                description = stripped[:100]
                                break
                skills.append(
                    {
                        "name": skill_name,
                        "package_dir": package_dir.name,
                        "description": description,
                        "scope": scope,
                    }
                )
            except Exception:
                skills.append({"name": skill_name, "package_dir": package_dir.name, "description": "（讀取失敗）", "scope": scope})

    collect(iter_skill_package_dirs(), "builtin")
    collect(iter_local_skill_package_dirs(), "local")

    builtin_count = sum(1 for item in skills if item["scope"] == "builtin")
    local_count = sum(1 for item in skills if item["scope"] == "local")

    return {
        "status": "success",
        "skills_dir": str(SKILLS_DIR),
        "skills_local_dir": str(LOCAL_SKILLS_DIR),
        "count": len(skills),
        "builtin_count": builtin_count,
        "local_count": local_count,
        "skills": skills,
        "message": f"共 {len(skills)} 個技能（builtin {builtin_count} / local {local_count}）",
    }


def main(argv: List[str] | None = None) -> int:
    args = argv or sys.argv
    if len(args) < 2:
        result = {
            "status": "success",
            "message": "GitHub 技能搜尋與下載工具（使用說明）",
            "help": True,
            "usage": {
                "search": "python .agent/skills/github-explorer/scripts/github_explorer.py search <keyword>",
                "preview": "python .agent/skills/github-explorer/scripts/github_explorer.py preview <repo_url> [skill_path]",
                "download": "python .agent/skills/github-explorer/scripts/github_explorer.py download <repo_url> <file_path> --confirm",
                "list": "python .agent/skills/github-explorer/scripts/github_explorer.py list",
                "rollback": "python .agent/skills/github-explorer/scripts/github_explorer.py rollback <skill_name>",
            },
            "security_note": "下載前必須先 preview 並取得使用者確認",
        }
        print(json.dumps(validate_output_schema(result, "github_explorer"), ensure_ascii=False, indent=2))
        return 0

    command = args[1].lower()
    if command == "search":
        if len(args) < 3:
            result = {
                "status": "error",
                "message": "請提供搜尋關鍵字",
                "usage": "python .agent/skills/github-explorer/scripts/github_explorer.py search <keyword>",
                "suggestion": "範例：python .agent/skills/github-explorer/scripts/github_explorer.py search crewai",
            }
            print(json.dumps(validate_output_schema(result, "github_explorer"), ensure_ascii=False, indent=2))
            return 1
        result = search_github_skills(" ".join(args[2:]))
    elif command == "preview":
        if len(args) < 3:
            result = {
                "status": "error",
                "message": "請提供 Repo URL",
                "usage": "python .agent/skills/github-explorer/scripts/github_explorer.py preview <repo_url> [skill_path]",
                "suggestion": "範例：python .agent/skills/github-explorer/scripts/github_explorer.py preview owner/repo",
            }
            print(json.dumps(validate_output_schema(result, "github_explorer"), ensure_ascii=False, indent=2))
            return 1
        result = preview_skill(args[2], args[3] if len(args) > 3 else "SKILL.md")
    elif command == "download":
        if len(args) < 4:
            result = {
                "status": "error",
                "message": "請提供 Repo URL 與檔案路徑",
                "usage": "python .agent/skills/github-explorer/scripts/github_explorer.py download <repo_url> <file_path> --confirm",
                "suggestion": "範例：python .agent/skills/github-explorer/scripts/github_explorer.py download owner/repo SKILL.md --confirm",
            }
            print(json.dumps(validate_output_schema(result, "github_explorer"), ensure_ascii=False, indent=2))
            return 1
        result = download_skill(args[2], args[3], user_confirmed="--confirm" in args)
    elif command == "list":
        result = list_local_skills()
    elif command == "rollback":
        if len(args) < 3:
            result = {
                "status": "error",
                "message": "請提供技能名稱",
                "usage": "python .agent/skills/github-explorer/scripts/github_explorer.py rollback <skill_name>",
                "suggestion": "範例：python .agent/skills/github-explorer/scripts/github_explorer.py rollback example_skill",
            }
            print(json.dumps(validate_output_schema(result, "github_explorer"), ensure_ascii=False, indent=2))
            return 1
        result = rollback_skill(args[2])
    else:
        result = {
            "status": "error",
            "message": f"未知指令：{command}",
            "available_commands": ["search", "preview", "download", "list", "rollback"],
            "usage": "python .agent/skills/github-explorer/scripts/github_explorer.py <command> [args]",
            "suggestion": "請先執行：python .agent/skills/github-explorer/scripts/github_explorer.py 以查看使用說明。",
        }
        print(json.dumps(validate_output_schema(result, "github_explorer"), ensure_ascii=False, indent=2))
        return 1

    print(json.dumps(validate_output_schema(result, "github_explorer"), ensure_ascii=False, indent=2))
    return 0 if result.get("status") in {"success", "pass", "warning"} else 1


__all__ = [
    "validate_output_schema",
    "write_audit_log",
    "check_whitelist",
    "calculate_file_hash",
    "add_to_manifest",
    "remove_from_manifest",
    "rollback_skill",
    "search_github_skills",
    "preview_skill",
    "download_skill",
    "run_conversion_pipeline",
    "run_security_scan",
    "list_local_skills",
    "main",
]


if __name__ == "__main__":
    raise SystemExit(main())
