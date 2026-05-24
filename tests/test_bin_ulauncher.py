from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
BIN_ULAUNCHER = REPO_ROOT / "bin/ulauncher"


def _stub_gapplication(tmp_path: Path, *, exit_code: int = 0) -> tuple[Path, dict[str, str]]:
    log_path = tmp_path / "gapplication.log"
    stub = tmp_path / "gapplication"
    stub.write_text(f"#!/bin/sh\nprintf '%s\\n' \"$@\" > {log_path}\nexit {exit_code}\n", encoding="utf-8")
    stub.chmod(0o755)
    env = os.environ.copy()
    env["PATH"] = f"{tmp_path}:{env['PATH']}"
    return log_path, env


@pytest.mark.parametrize(
    ("flag", "hint"),
    [
        ("--hide-window", "use start"),
        ("--no-extensions", "see --help for available commands"),
        ("--no-window-shadow", "the Window shadow size setting"),
    ],
)
def test_legacy_terminal_flags_exit_without_python(flag: str, hint: str) -> None:
    result = subprocess.run([str(BIN_ULAUNCHER), flag], capture_output=True, text=True, check=False)
    assert result.returncode == 2
    assert flag in result.stderr
    assert hint in result.stderr
    assert result.stdout == ""


@pytest.mark.parametrize(
    ("legacy", "replacement"),
    [
        ("--dev", "--verbose"),
        ("--daemon", "start"),
        ("--no-window", "start"),
    ],
)
def test_legacy_rewrite_flags_substitute_and_warn(legacy: str, replacement: str, tmp_path: Path) -> None:
    # Stub `python3` to record argv and exit; that lets us assert what the wrapper hands to python.
    log_path = tmp_path / "python.log"
    stub = tmp_path / "python3"
    stub.write_text(f"#!/bin/sh\nprintf '%s\\n' \"$@\" > {log_path}\n", encoding="utf-8")
    stub.chmod(0o755)

    env = {"PATH": f"{tmp_path}:/usr/bin:/bin"}
    result = subprocess.run([str(BIN_ULAUNCHER), legacy], capture_output=True, text=True, env=env, check=False)

    assert legacy in result.stderr
    forwarded = log_path.read_text(encoding="utf-8").splitlines()
    assert "-m" in forwarded
    assert "ulauncher" in forwarded
    assert replacement in forwarded
    assert legacy not in forwarded


@pytest.mark.parametrize(
    ("argv", "expected_lines"),
    [
        ([], ["action", "io.ulauncher.Ulauncher", "show-window"]),
        (["show"], ["action", "io.ulauncher.Ulauncher", "show-window"]),
        (["show", "foo bar"], ["action", "io.ulauncher.Ulauncher", "set-query", "'foo bar'"]),
        (["show", "Tony's app"], ["action", "io.ulauncher.Ulauncher", "set-query", "'Tony\\'s app'"]),
        (["show", "back\\slash"], ["action", "io.ulauncher.Ulauncher", "set-query", "'back\\\\slash'"]),
        (["toggle"], ["action", "io.ulauncher.Ulauncher", "toggle-window"]),
    ],
)
def test_fast_path_execs_gapplication(tmp_path: Path, argv: list[str], expected_lines: list[str]) -> None:
    log_path, env = _stub_gapplication(tmp_path)
    subprocess.run([str(BIN_ULAUNCHER), *argv], check=True, env=env)
    assert log_path.read_text(encoding="utf-8").splitlines() == expected_lines


@pytest.mark.parametrize(
    "argv",
    [
        ["--version"],
        ["--help"],
        ["-h"],
        ["show", "--help"],
        ["show", "--verbose"],
        ["start"],
        ["extensions"],
        ["show", "foo", "bar"],  # extra positional disqualifies fast path
    ],
)
def test_fast_path_defers_to_python(tmp_path: Path, argv: list[str]) -> None:
    # When the fast path can't handle argv, gapplication must NOT be exec'd; control should
    # reach the Python invocation (which we stub via PATH to a no-op python3 to keep the test
    # offline-fast).
    log_path, env = _stub_gapplication(tmp_path)
    python_stub = tmp_path / "python3"
    python_stub.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    python_stub.chmod(0o755)

    subprocess.run([str(BIN_ULAUNCHER), *argv], check=False, env=env)

    assert not log_path.exists(), f"fast path should not have run gapplication for {argv!r}"
