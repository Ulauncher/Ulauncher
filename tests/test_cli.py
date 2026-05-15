import pytest
from pytest_mock import MockerFixture

from ulauncher import cli


class TestCLI:
    def test_parse_empty_args_defaults(self, capsys: pytest.CaptureFixture[str]) -> None:
        args = cli.parse([])

        assert args.daemon is False
        assert args.verbose is False
        assert args.command is None
        assert capsys.readouterr().out == ""

    def test_parse_no_window_maps_to_daemon(self, capsys: pytest.CaptureFixture[str]) -> None:
        args = cli.parse(["--no-window"])

        assert args.daemon is True
        assert not hasattr(args, "no_window")
        assert "use --daemon" in capsys.readouterr().err

    def test_parse_dev_maps_to_verbose(self, capsys: pytest.CaptureFixture[str]) -> None:
        args = cli.parse(["--dev"])

        assert args.verbose is True
        assert not hasattr(args, "dev")
        assert "use --verbose" in capsys.readouterr().err

    def test_parse_hide_window_exits(self, capsys: pytest.CaptureFixture[str]) -> None:
        with pytest.raises(SystemExit) as exc_info:
            cli.parse(["--hide-window"])
        assert exc_info.value.code == 2
        assert "use --daemon" in capsys.readouterr().err

    def test_parse_no_extensions_exits(self, capsys: pytest.CaptureFixture[str]) -> None:
        with pytest.raises(SystemExit) as exc_info:
            cli.parse(["--no-extensions"])
        assert exc_info.value.code == 2
        assert "see --help for available commands" in capsys.readouterr().err

    def test_parse_no_window_shadow_exits(self) -> None:
        with pytest.raises(SystemExit) as exc_info:
            cli.parse(["--no-window-shadow"])
        assert exc_info.value.code == 2

    def test_parse_upgrade_normalizes_alias(self, capsys: pytest.CaptureFixture[str]) -> None:
        args = cli.parse(["up"])

        assert args.command == "upgrade"
        assert capsys.readouterr().out == ""

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
