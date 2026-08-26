from __future__ import annotations

import os
import shlex
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
BIN_ULAUNCHER = REPO_ROOT / "bin/ulauncher"


def _write_stub(path: Path, *, stdout: str = "", stderr: str = "", exit_code: int = 0) -> Path:
    """Create an executable that logs its argv to <name>.log, then prints and exits as told."""
    log_path = path.with_suffix(".log")
    script = f"#!/bin/sh\nprintf '%s\\n' \"$@\" > {log_path}\n"
    if stdout:
        script += f"printf '%s\\n' {shlex.quote(stdout)}\n"
    if stderr:
        script += f"printf '%s\\n' {shlex.quote(stderr)} >&2\n"
    path.write_text(f"{script}exit {exit_code}\n", encoding="utf-8")
    path.chmod(0o755)
    return log_path


def _stub_gapplication(
    tmp_path: Path,
    *,
    exit_code: int = 0,
    stderr: str = "",
    name_has_owner: bool = True,
) -> tuple[Path, dict[str, str]]:
    # A bare invocation from a checkout (which is how the suite runs it) consults gdbus, so stub
    # it too and default to "an instance is already running".
    _write_stub(tmp_path / "gdbus", stdout=f"({str(name_has_owner).lower()},)")
    log_path = _write_stub(tmp_path / "gapplication", stderr=stderr, exit_code=exit_code)
    env = os.environ.copy()
    env["PATH"] = f"{tmp_path}:{env['PATH']}"
    return log_path, env


@pytest.mark.parametrize(
    ("flag", "hint"),
    [
        ("--hide-window", "use start"),
        ("--autostart-method-xdg", ""),
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


# dbus-daemon and dbus-broker word the same ServiceUnknown error differently.
GDBUS_ERROR_PREFIX = "error sending ActivateAction message to application: GDBus.Error:"
SERVICE_UNKNOWN_ERRORS = [
    (
        f"{GDBUS_ERROR_PREFIX}org.freedesktop.DBus.Error.ServiceUnknown: "
        "The name io.ulauncher.Ulauncher was not provided by any .service files"
    ),
    f"{GDBUS_ERROR_PREFIX}org.freedesktop.DBus.Error.ServiceUnknown: The name is not activatable",
]


@pytest.mark.parametrize("error", SERVICE_UNKNOWN_ERRORS)
@pytest.mark.parametrize("argv", [[], ["show"], ["show", "foo"], ["toggle"]])
def test_service_unknown_reports_that_ulauncher_is_not_running(tmp_path: Path, argv: list[str], error: str) -> None:
    _, env = _stub_gapplication(tmp_path, exit_code=1, stderr=error)
    result = subprocess.run([str(BIN_ULAUNCHER), *argv], capture_output=True, text=True, env=env, check=False)

    assert result.returncode == 1
    assert "Ulauncher is not running" in result.stderr
    assert "ulauncher start" in result.stderr
    assert "systemctl --user enable --now ulauncher" in result.stderr
    assert "GDBus.Error" not in result.stderr


def test_other_gapplication_errors_pass_through_unchanged(tmp_path: Path) -> None:
    _, env = _stub_gapplication(tmp_path, exit_code=3, stderr="some other failure")
    result = subprocess.run([str(BIN_ULAUNCHER)], capture_output=True, text=True, env=env, check=False)

    assert result.returncode == 3
    assert "some other failure" in result.stderr
    assert "Ulauncher is not running" not in result.stderr


def test_bare_invocation_from_a_checkout_starts_it_rather_than_the_installed_ulauncher(tmp_path: Path) -> None:
    gapplication_log, env = _stub_gapplication(tmp_path, name_has_owner=False)
    python_log = _write_stub(tmp_path / "python3")

    result = subprocess.run([str(BIN_ULAUNCHER)], capture_output=True, text=True, env=env, check=False)

    assert "starting this checkout" in result.stderr
    assert not gapplication_log.exists(), "D-Bus activation would have started the installed Ulauncher"
    assert python_log.read_text(encoding="utf-8").splitlines() == ["-m", "ulauncher", "start"]


@pytest.mark.parametrize("argv", [["show"], ["show", "foo"], ["toggle"]])
def test_explicit_show_and_toggle_never_start_ulauncher(tmp_path: Path, argv: list[str]) -> None:
    _, env = _stub_gapplication(tmp_path, exit_code=1, stderr=SERVICE_UNKNOWN_ERRORS[0], name_has_owner=False)
    python_log = _write_stub(tmp_path / "python3")

    result = subprocess.run([str(BIN_ULAUNCHER), *argv], capture_output=True, text=True, env=env, check=False)

    assert result.returncode == 1
    assert "Ulauncher is not running" in result.stderr
    assert not python_log.exists()


def test_installed_ulauncher_activates_without_asking_dbus_for_the_name_owner(tmp_path: Path) -> None:
    # An install has no `ulauncher` package dir next to bin/, so the checkout branch is skipped
    # and the fast path stays a single gapplication call.
    install_root = tmp_path / "install"
    (install_root / "bin").mkdir(parents=True)
    installed_bin = install_root / "bin/ulauncher"
    installed_bin.write_bytes(BIN_ULAUNCHER.read_bytes())
    installed_bin.chmod(0o755)

    gapplication_log, env = _stub_gapplication(tmp_path, name_has_owner=False)
    subprocess.run([str(installed_bin)], check=True, env=env)

    assert gapplication_log.read_text(encoding="utf-8").splitlines() == [
        "action",
        "io.ulauncher.Ulauncher",
        "show-window",
    ]
    assert not (tmp_path / "gdbus.log").exists()


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
