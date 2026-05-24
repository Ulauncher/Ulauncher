from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
BIN_ULAUNCHER = REPO_ROOT / "bin/ulauncher"


@pytest.mark.parametrize(
    ("flag", "hint"),
    [
        ("--hide-window", "use --daemon"),
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
        ("--no-window", "--daemon"),
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
