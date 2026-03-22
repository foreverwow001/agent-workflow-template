# -*- coding: utf-8 -*-
"""
tests/test_bootstrap_hardening_regression.py
===========================================
用途：驗證 bootstrap hardening shell scripts 的最低契約不會退化
職責：
  - 驗證 install_workflow_prereqs.sh 的 check-only 與 ready path
    - 驗證 post_create.sh 仍會串接 prereq、Obsidian single-root exposure、Python bootstrap 與 terminal tooling
  - 驗證 install_terminal_tooling.sh 仍會自動安裝缺失 CLI 並建立 local extension symlink
===========================================
"""

from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PREREQ_SCRIPT = REPO_ROOT / ".agent" / "runtime" / "scripts" / "install_workflow_prereqs.sh"
POST_CREATE_SCRIPT = REPO_ROOT / ".agent" / "runtime" / "scripts" / "devcontainer" / "post_create.sh"
TERMINAL_TOOLING_SCRIPT = REPO_ROOT / ".agent" / "runtime" / "scripts" / "vscode" / "install_terminal_tooling.sh"


def write_executable(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    path.chmod(0o755)


def copy_script(source: Path, repo_root: Path, relative_path: str) -> Path:
    target = repo_root / relative_path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
    target.chmod(0o755)
    return target


def run_script(script_path: Path, cwd: Path, env: dict[str, str], *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["/bin/bash", str(script_path), *args],
        cwd=str(cwd),
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


class BootstrapHardeningRegressionTest(unittest.TestCase):
    def test_install_workflow_prereqs_check_only_reports_missing_dependencies(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            script_path = copy_script(
                PREREQ_SCRIPT,
                repo_root,
                ".agent/runtime/scripts/install_workflow_prereqs.sh",
            )

            fake_bin = repo_root / "fake-bin"
            fake_bin.mkdir(parents=True, exist_ok=True)
            write_executable(fake_bin / "uname", "#!/usr/bin/env bash\n/bin/uname \"$@\"\n")

            env = {
                "HOME": str(repo_root / "home"),
                "PATH": str(fake_bin),
            }

            result = run_script(script_path, repo_root, env, "--check-only")

        self.assertEqual(result.returncode, 1, result)
        self.assertIn("Git missing: git", result.stderr)
        self.assertIn("Python with venv support missing.", result.stderr)
        self.assertIn("Codex CLI missing: codex", result.stderr)
        self.assertIn("Copilot CLI missing: copilot", result.stderr)
        self.assertIn("Missing dependencies remain:", result.stderr)

    def test_install_workflow_prereqs_succeeds_when_all_required_commands_exist(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            script_path = copy_script(
                PREREQ_SCRIPT,
                repo_root,
                ".agent/runtime/scripts/install_workflow_prereqs.sh",
            )

            fake_bin = repo_root / "fake-bin"
            fake_bin.mkdir(parents=True, exist_ok=True)
            write_executable(fake_bin / "uname", "#!/usr/bin/env bash\n/bin/uname \"$@\"\n")
            for command_name in ["git", "node", "npm", "codex", "copilot", "bwrap"]:
                write_executable(fake_bin / command_name, "#!/usr/bin/env bash\nexit 0\n")
            write_executable(
                fake_bin / "python",
                "#!/usr/bin/env bash\n"
                "if [[ \"${1:-}\" == \"-m\" && \"${2:-}\" == \"venv\" && \"${3:-}\" == \"--help\" ]]; then\n"
                "  exit 0\n"
                "fi\n"
                "exit 0\n",
            )

            env = {
                "HOME": str(repo_root / "home"),
                "PATH": f"{fake_bin}:/usr/bin:/bin",
            }

            result = run_script(script_path, repo_root, env)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Minimum workflow dependencies are ready.", result.stdout)

    def test_post_create_runs_prereqs_python_bootstrap_and_terminal_tooling(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            script_path = copy_script(
                POST_CREATE_SCRIPT,
                repo_root,
                ".agent/runtime/scripts/devcontainer/post_create.sh",
            )
            log_path = repo_root / "post-create.log"
            vault_root = repo_root / "mounted-vault"
            vault_root.mkdir(parents=True, exist_ok=True)

            write_executable(
                repo_root / ".agent/runtime/scripts/install_workflow_prereqs.sh",
                "#!/usr/bin/env bash\n"
                "echo prereqs >> \"$POST_CREATE_LOG\"\n",
            )
            write_executable(
                repo_root / ".agent/runtime/scripts/vscode/install_terminal_tooling.sh",
                "#!/usr/bin/env bash\n"
                "echo tooling >> \"$POST_CREATE_LOG\"\n",
            )

            fake_bin = repo_root / "fake-bin"
            fake_bin.mkdir(parents=True, exist_ok=True)
            write_executable(
                fake_bin / "python",
                "#!/usr/bin/env bash\n"
                "set -e\n"
                "if [[ \"${1:-}\" == \"-m\" && \"${2:-}\" == \"venv\" ]]; then\n"
                "  venv_dir=\"$3\"\n"
                "  mkdir -p \"$venv_dir/bin\"\n"
                "  cat > \"$venv_dir/bin/python\" <<'EOF'\n"
                "#!/usr/bin/env bash\n"
                "echo \"venv_python:$*\" >> \"$POST_CREATE_LOG\"\n"
                "exit 0\n"
                "EOF\n"
                "  chmod +x \"$venv_dir/bin/python\"\n"
                "  cat > \"$venv_dir/bin/uv\" <<'EOF'\n"
                "#!/usr/bin/env bash\n"
                "echo \"uv:$*\" >> \"$POST_CREATE_LOG\"\n"
                "exit 0\n"
                "EOF\n"
                "  chmod +x \"$venv_dir/bin/uv\"\n"
                "  echo \"create_venv:$venv_dir\" >> \"$POST_CREATE_LOG\"\n"
                "  exit 0\n"
                "fi\n"
                "echo \"python:$*\" >> \"$POST_CREATE_LOG\"\n"
                "exit 0\n",
            )

            env = {
                "HOME": str(repo_root / "home"),
                "PATH": f"{fake_bin}:/usr/bin:/bin",
                "POST_CREATE_LOG": str(log_path),
                "OBSIDIAN_VAULT_ROOT": str(vault_root),
                "UV_VERSION": "0.5.24",
            }

            result = run_script(script_path, repo_root, env)
            log_lines = log_path.read_text(encoding="utf-8").splitlines()
            obsidian_link = repo_root / "obsidian-vault"
            obsidian_link_exists = obsidian_link.is_symlink()
            obsidian_link_target = obsidian_link.resolve() if obsidian_link_exists else None

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(log_lines[0], "prereqs")
        self.assertTrue(obsidian_link_exists)
        self.assertEqual(obsidian_link_target, vault_root)
        self.assertTrue(log_lines[1].startswith("create_venv:"), log_lines)
        self.assertIn("venv_python:-m pip install --upgrade pip", log_lines)
        self.assertIn("venv_python:-m pip install --no-cache-dir uv==0.5.24", log_lines)
        self.assertEqual(log_lines[-1], "tooling")
        self.assertIn("Linked obsidian-vault ->", result.stdout)
        self.assertIn("No Python dependency manifest found; skipping dependency install.", result.stdout)

    def test_install_terminal_tooling_auto_installs_missing_clis_and_links_extensions(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            script_path = copy_script(
                TERMINAL_TOOLING_SCRIPT,
                repo_root,
                ".agent/runtime/scripts/vscode/install_terminal_tooling.sh",
            )
            log_path = repo_root / "terminal-tooling.log"
            npm_prefix = repo_root / "npm-prefix"
            npm_prefix.mkdir(parents=True, exist_ok=True)

            pty_dir = repo_root / ".agent/runtime/tools/vscode_terminal_pty"
            fallback_dir = repo_root / ".agent/runtime/tools/vscode_terminal_fallback"
            pty_dir.mkdir(parents=True, exist_ok=True)
            fallback_dir.mkdir(parents=True, exist_ok=True)
            (pty_dir / "package.json").write_text('{"version": "1.2.3"}\n', encoding="utf-8")
            (fallback_dir / "package.json").write_text('{"version": "4.5.6"}\n', encoding="utf-8")

            fake_bin = repo_root / "fake-bin"
            fake_bin.mkdir(parents=True, exist_ok=True)
            write_executable(
                fake_bin / "npm",
                "#!/usr/bin/env bash\n"
                "echo \"npm:$*\" >> \"$TERMINAL_TOOLING_LOG\"\n"
                "if [[ \"${1:-}\" == \"prefix\" && \"${2:-}\" == \"-g\" ]]; then\n"
                "  printf '%s\\n' \"$FAKE_NPM_PREFIX\"\n"
                "  exit 0\n"
                "fi\n"
                "exit 0\n",
            )

            home_dir = repo_root / "home"
            ext_dir = home_dir / ".vscode-server-insiders" / "extensions"
            ext_dir.mkdir(parents=True, exist_ok=True)

            env = {
                "HOME": str(home_dir),
                "PATH": f"{fake_bin}:/usr/bin:/bin",
                "TERMINAL_TOOLING_LOG": str(log_path),
                "FAKE_NPM_PREFIX": str(npm_prefix),
            }

            result = run_script(script_path, repo_root, env)
            log_text = log_path.read_text(encoding="utf-8")
            pty_link = ext_dir / "ivyhouse-local.ivyhouse-terminal-pty-1.2.3"
            fallback_link = ext_dir / "ivyhouse-local.ivyhouse-terminal-fallback-4.5.6"
            pty_link_exists = pty_link.is_symlink()
            pty_link_target = pty_link.resolve() if pty_link_exists else None
            fallback_link_exists = fallback_link.is_symlink()
            fallback_link_target = fallback_link.resolve() if fallback_link_exists else None

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("npm:install -g @openai/codex", log_text)
        self.assertIn("npm:install -g @github/copilot", log_text)
        self.assertTrue(pty_link_exists)
        self.assertEqual(pty_link_target, pty_dir)
        self.assertTrue(fallback_link_exists)
        self.assertEqual(fallback_link_target, fallback_dir)
        self.assertIn("Developer: Reload Window", result.stdout)


if __name__ == "__main__":
    unittest.main()
