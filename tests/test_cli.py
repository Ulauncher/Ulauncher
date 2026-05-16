from __future__ import annotations

import pytest
from pytest_mock import MockerFixture

from ulauncher import cli


def assert_cli_args(args: cli.CLIArguments, expected_attrs: dict[str, object]) -> None:
    for attr, value in expected_attrs.items():
        assert getattr(args, attr) == value


class TestCLIParse:
    @pytest.mark.parametrize(
        ("input_args", "expected_attrs"),
        [
            pytest.param(
                [],
                {"command": None, "verbose": False, "daemon": False},
                id="defaults",
            ),
            pytest.param(["--daemon"], {"command": None, "daemon": True}, id="daemon"),
            pytest.param(["--verbose"], {"command": None, "verbose": True}, id="verbose"),
            pytest.param(["-v"], {"command": None, "verbose": True}, id="v-short"),
            pytest.param(["extensions"], {"command": "extensions"}, id="extensions"),
            pytest.param(["install", "git://example"], {"command": "install", "input": "git://example"}, id="install"),
            pytest.param(["uninstall", "ext-id"], {"command": "uninstall", "input": "ext-id"}, id="uninstall"),
            pytest.param(["upgrade"], {"command": "upgrade", "input": ""}, id="upgrade-all"),
            pytest.param(["upgrade", "ext-id"], {"command": "upgrade", "input": "ext-id"}, id="upgrade-one"),
            pytest.param(["preview", "/tmp/demo"], {"command": "preview", "path": "/tmp/demo"}, id="preview"),
            pytest.param(
                ["preview", "--with-debugger", "/tmp/demo"],
                {"command": "preview", "path": "/tmp/demo", "with_debugger": True},
                id="preview-with-debugger",
            ),
        ],
    )
    def test_parse_commands(
        self,
        input_args: list[str],
        expected_attrs: dict[str, object],
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        args = cli.parse(input_args)

        assert_cli_args(args, expected_attrs)

        captured = capsys.readouterr()
        assert captured.out == ""
        assert captured.err == ""

    @pytest.mark.parametrize(
        ("input_args", "expected_attrs"),
        [
            pytest.param(["e"], {"command": "extensions"}, id="extensions"),
            pytest.param(["i", "git://example"], {"command": "install", "input": "git://example"}, id="install"),
            pytest.param(["rm", "ext-id"], {"command": "uninstall", "input": "ext-id"}, id="uninstall"),
            pytest.param(["up"], {"command": "upgrade", "input": ""}, id="upgrade"),
            pytest.param(["pr", "/tmp/demo"], {"command": "preview", "path": "/tmp/demo"}, id="preview"),
        ],
    )
    def test_parse_command_aliases(
        self,
        input_args: list[str],
        expected_attrs: dict[str, object],
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        args = cli.parse(input_args)

        assert_cli_args(args, expected_attrs)

        captured = capsys.readouterr()
        assert captured.out == ""
        assert captured.err == ""

    @pytest.mark.parametrize(
        ("input_args", "expected_attrs", "removed_attr", "stderr_substring"),
        [
            pytest.param(
                ["--no-window"], {"command": None, "daemon": True}, "no_window", "use --daemon", id="no-window"
            ),
            pytest.param(["--dev"], {"command": None, "verbose": True}, "dev", "use --verbose", id="dev"),
        ],
    )
    def test_parse_legacy_argument_shims(
        self,
        input_args: list[str],
        expected_attrs: dict[str, object],
        removed_attr: str,
        stderr_substring: str,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        args = cli.parse(input_args)

        assert_cli_args(args, expected_attrs)
        assert not hasattr(args, removed_attr)

        captured = capsys.readouterr()
        assert captured.out == ""
        assert stderr_substring in captured.err

    @pytest.mark.parametrize(
        ("input_args", "stderr_substring"),
        [
            pytest.param(["--hide-window"], "use --daemon", id="hide-window"),
            pytest.param(["--no-extensions"], "see --help for available commands", id="no-extensions"),
            pytest.param(["--no-window-shadow"], "the Window shadow size setting", id="no-window-shadow"),
        ],
    )
    def test_parse_errors(
        self,
        input_args: list[str],
        stderr_substring: str,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        with pytest.raises(SystemExit) as exc_info:
            cli.parse(input_args)

        assert exc_info.value.code == 2

        captured = capsys.readouterr()
        assert captured.out == ""
        assert stderr_substring in captured.err


class TestCLIRunCommand:
    def test_run_command_dispatches_default_app_handler(self, mocker: MockerFixture) -> None:
        ensure_runtime_dirs = mocker.patch("ulauncher.cli.ensure_runtime_dirs")
        mocker.patch("ulauncher.cli.configure_logging")
        handler = mocker.Mock(return_value=True)
        load_handler = mocker.patch("ulauncher.cli._load_handler", return_value=handler)

        args = cli.parse([])

        assert cli.run_command(args) is True

        ensure_runtime_dirs.assert_called_once_with()
        load_handler.assert_called_once_with("ulauncher.cli.commands.app:run")
        handler.assert_called_once_with(args)
