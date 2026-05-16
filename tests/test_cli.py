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
                {"command": "show", "verbose": False, "input": "", "path": "", "query": None, "with_debugger": False},
                id="defaults-to-show",
            ),
            pytest.param(["show"], {"command": "show", "query": None}, id="show"),
            pytest.param(["show", "foo"], {"command": "show", "query": "foo"}, id="show-with-query"),
            pytest.param(["toggle"], {"command": "toggle"}, id="toggle"),
            pytest.param(["--verbose"], {"command": "show", "verbose": True}, id="verbose-default-command"),
            pytest.param(["start"], {"command": "start"}, id="start"),
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


class TestCLIRunCommand:
    @pytest.mark.parametrize(
        ("input_args", "command_name", "logging_mode"),
        [
            pytest.param([], "show", None, id="show"),
            pytest.param(["toggle"], "toggle", None, id="toggle"),
            pytest.param(["start"], "start", "app", id="start"),
            pytest.param(["extensions"], "extensions", "cli", id="extensions"),
        ],
    )
    def test_run_command_dispatches_handler_with_expected_bootstrap_mode(
        self,
        input_args: list[str],
        command_name: str,
        logging_mode: str | None,
        mocker: MockerFixture,
    ) -> None:
        ensure_runtime_dirs = mocker.patch("ulauncher.cli.ensure_runtime_dirs")
        configure_logging = mocker.patch("ulauncher.cli.configure_logging")
        handler = mocker.Mock(return_value=True)
        load_handler = mocker.patch("ulauncher.cli._load_handler", return_value=handler)

        args = cli.parse(input_args)

        assert cli.run_command(args) is True

        if logging_mode is not None:
            ensure_runtime_dirs.assert_called_once_with()
            configure_logging.assert_called_once_with(verbose=False, use_app_logging=logging_mode == "app")
        else:
            ensure_runtime_dirs.assert_not_called()
            configure_logging.assert_not_called()

        load_handler.assert_called_once_with(command_name)
        handler.assert_called_once_with(args)


class TestCLIHelp:
    def test_groups_top_level_commands_in_help_output(self) -> None:
        help_text = cli._get_parser().format_help()
        start_summary = cli._get_commands()["start"].summary

        app_group_index = help_text.index("App commands:")
        show_index = help_text.index("Show the Ulauncher window (default command)")
        help_index = help_text.index("Show help")
        extension_group_index = help_text.index("Extension commands:")
        extensions_index = help_text.index("List installed extensions")
        preview_index = help_text.index("Preview extension")

        assert app_group_index < show_index < help_index < extension_group_index < extensions_index < preview_index
        assert "Available commands" not in help_text
        assert "Options:" not in help_text
        assert "\nApp commands:\n  start" in help_text
        assert "\nExtension commands:\n  extensions (e)" in help_text
        assert f"start {start_summary}" in " ".join(help_text.split())

    def test_subcommand_help_does_not_repeat_top_level_command_groups(self, capsys: pytest.CaptureFixture[str]) -> None:
        with pytest.raises(SystemExit) as exc_info:
            cli.parse(["show", "--help"])

        assert exc_info.value.code == 0

        captured = capsys.readouterr()
        assert "App commands:" not in captured.out
        assert "Extension commands:" not in captured.out
        assert "\nOptions:\n" in captured.out
        assert captured.err == ""
