#!/usr/bin/env python3
import argparse
import fcntl
import json
import os
import pty
import select
import shlex
import signal
import struct
import subprocess
import sys
import termios
import time


def set_winsize(fd: int, rows: int, cols: int) -> None:
    winsize = struct.pack("HHHH", max(1, rows), max(1, cols), 0, 0)
    fcntl.ioctl(fd, termios.TIOCSWINSZ, winsize)


def maybe_open_control_fd(fd: int) -> int | None:
    try:
        os.fstat(fd)
    except OSError:
        return None
    return fd


def handle_control_message(proc: subprocess.Popen[bytes], master_fd: int, payload: bytes) -> None:
    if not payload.strip():
        return

    try:
        message = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return

    if message.get("type") != "resize":
        return

    rows = int(message.get("rows") or 0)
    cols = int(message.get("cols") or 0)
    if rows <= 0 or cols <= 0:
        return

    set_winsize(master_fd, rows, cols)
    try:
        os.killpg(proc.pid, signal.SIGWINCH)
    except ProcessLookupError:
        pass


def signal_process_group(proc: subprocess.Popen[bytes], signum: int) -> None:
    try:
        os.killpg(proc.pid, signum)
    except ProcessLookupError:
        pass


def close_fd(fd: int | None) -> int | None:
    if fd is None:
        return None
    try:
        os.close(fd)
    except OSError:
        pass
    return None


def resolve_command_for_spawn(command: list[str]) -> list[str]:
    if not command:
        return command

    candidate = command[0]
    if not os.path.isfile(candidate):
        return command

    try:
        with open(candidate, "rb") as handle:
            header = handle.read(256)
    except OSError:
        return command

    if not header.startswith(b"#!"):
        return command

    try:
        shebang = header.splitlines()[0].decode("utf-8", errors="ignore")[2:].strip()
    except IndexError:
        return command

    if not shebang:
        return command

    try:
        interpreter_command = shlex.split(shebang)
    except ValueError:
        return command

    if not interpreter_command:
        return command

    # Open shebang scripts through their interpreter to avoid ETXTBSY when VS Code
    # extensions update wrapper scripts during window reload or startup.
    return [*interpreter_command, candidate, *command[1:]]


def forward_stream(
    proc: subprocess.Popen[bytes],
    master_fd: int | None,
    control_fd: int | None,
    shutdown_state: dict[str, float | bool | None],
) -> int:
    stdin_fd = sys.stdin.fileno()
    stdin_open = True
    master_open = master_fd is not None
    control_open = control_fd is not None
    control_buffer = b""

    def advance_shutdown(now: float) -> None:
        nonlocal master_fd, master_open, control_fd, control_open
        if shutdown_state["requested_at"] is None or proc.poll() is not None:
            return

        if not shutdown_state["hup_sent"]:
            signal_process_group(proc, signal.SIGHUP)
            signal_process_group(proc, signal.SIGCONT)
            shutdown_state["hup_sent"] = True

        elapsed = now - float(shutdown_state["requested_at"])

        if elapsed >= 0.1 and master_open:
            master_fd = close_fd(master_fd)
            master_open = False

        if elapsed >= 0.1 and control_open:
            control_fd = close_fd(control_fd)
            control_open = False

        if elapsed >= 0.2 and not shutdown_state["term_sent"]:
            signal_process_group(proc, signal.SIGTERM)
            shutdown_state["term_sent"] = True

        if elapsed >= 0.35 and not shutdown_state["kill_sent"]:
            signal_process_group(proc, signal.SIGKILL)
            shutdown_state["kill_sent"] = True

    while master_open or proc.poll() is None:
        if shutdown_state["requested_at"] is not None:
            advance_shutdown(time.monotonic())

        read_fds = [master_fd] if master_open else []
        if stdin_open:
            read_fds.append(stdin_fd)
        if control_open and control_fd is not None:
            read_fds.append(control_fd)

        if not read_fds:
            break

        ready, _, _ = select.select(read_fds, [], [], 0.1)

        if shutdown_state["requested_at"] is not None:
            advance_shutdown(time.monotonic())

        if master_open and master_fd in ready:
            try:
                data = os.read(master_fd, 65536)
            except OSError:
                data = b""
            if data:
                sys.stdout.buffer.write(data)
                sys.stdout.buffer.flush()
            else:
                master_open = False

        if stdin_open and stdin_fd in ready:
            data = os.read(stdin_fd, 65536)
            if not data:
                stdin_open = False
            elif master_fd is None:
                stdin_open = False
            else:
                try:
                    os.write(master_fd, data)
                except OSError:
                    stdin_open = False

        if control_open and control_fd is not None and control_fd in ready:
            try:
                data = os.read(control_fd, 65536)
            except OSError:
                data = b""

            if not data:
                control_open = False
            else:
                control_buffer += data
                while b"\n" in control_buffer:
                    raw_message, control_buffer = control_buffer.split(b"\n", 1)
                    handle_control_message(proc, master_fd, raw_message)

    return proc.wait()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cwd", required=True)
    parser.add_argument("--cols", type=int, default=160)
    parser.add_argument("--rows", type=int, default=40)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()

    command = list(args.command)
    if command and command[0] == "--":
        command = command[1:]

    if not command:
        print("[pty-bridge] missing command", file=sys.stderr, flush=True)
        return 2

    command = resolve_command_for_spawn(command)

    master_fd, slave_fd = pty.openpty()
    set_winsize(slave_fd, args.rows, args.cols)

    env = os.environ.copy()
    env.setdefault("TERM", "xterm-256color")
    env.setdefault("COLORTERM", "truecolor")
    env["COLUMNS"] = str(args.cols)
    env["LINES"] = str(args.rows)

    try:
        proc = subprocess.Popen(
            command,
            stdin=slave_fd,
            stdout=slave_fd,
            stderr=slave_fd,
            cwd=args.cwd,
            env=env,
            start_new_session=True,
        )
    except FileNotFoundError:
        os.close(slave_fd)
        os.close(master_fd)
        missing_command = command[0] if command else ""
        print(f"[pty-bridge] command not found: {missing_command}", file=sys.stderr, flush=True)
        print(
            "[pty-bridge] install the CLI or update the VS Code PTY command setting for this backend.",
            file=sys.stderr,
            flush=True,
        )
        return 127
    os.close(slave_fd)
    control_fd = maybe_open_control_fd(3)
    shutdown_state: dict[str, float | bool | None] = {
        "requested_at": None,
        "hup_sent": False,
        "term_sent": False,
        "kill_sent": False,
    }

    def terminate(signum: int, _frame) -> None:
        if signum == signal.SIGTERM:
            if shutdown_state["requested_at"] is None:
                shutdown_state["requested_at"] = time.monotonic()
            return
        signal_process_group(proc, signum)

    signal.signal(signal.SIGTERM, terminate)
    signal.signal(signal.SIGINT, terminate)

    try:
        return forward_stream(proc, master_fd, control_fd, shutdown_state)
    finally:
        if proc.poll() is None:
            signal_process_group(proc, signal.SIGKILL)
            try:
                proc.wait(timeout=0.2)
            except subprocess.TimeoutExpired:
                pass
        close_fd(master_fd)
        close_fd(control_fd)


if __name__ == "__main__":
    raise SystemExit(main())
