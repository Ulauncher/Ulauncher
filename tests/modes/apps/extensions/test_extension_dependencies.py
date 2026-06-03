from __future__ import annotations

import subprocess
import sys
from typing import Any, Callable
from unittest.mock import MagicMock, mock_open

import pytest
from pytest_mock import MockerFixture

from ulauncher.modes.extensions import ext_exceptions
from ulauncher.modes.extensions.extension_dependencies import ExtensionDependencies


@pytest.fixture
def extension_dependencies() -> ExtensionDependencies:
    return ExtensionDependencies(ext_id="extension-X", path="/fake/path")


@pytest.fixture
def isfile(mocker: MockerFixture) -> Callable[..., bool]:
    return mocker.patch("ulauncher.modes.extensions.extension_dependencies.isfile")


@pytest.fixture
def isdir(mocker: MockerFixture) -> Callable[..., bool]:
    return mocker.patch("ulauncher.modes.extensions.extension_dependencies.isdir")


@pytest.fixture
def builtins_open(mocker: MockerFixture) -> Any:
    return mocker.patch("builtins.open", new_callable=mock_open, read_data="some-package==1.0\n")


@pytest.fixture
def run_command(mocker: MockerFixture) -> MagicMock:
    return mocker.patch("ulauncher.modes.extensions.extension_dependencies.run_command")


@pytest.mark.usefixtures("isfile", "isdir")
def test_get_dependencies_path(
    extension_dependencies: ExtensionDependencies,
) -> None:
    deps_path = extension_dependencies.get_dependencies_path()
    assert deps_path == "/fake/path/.dependencies"


@pytest.mark.usefixtures("builtins_open")
def test_install(
    run_command: MagicMock,
    extension_dependencies: ExtensionDependencies,
    isfile: MagicMock,
) -> None:
    isfile.return_value = True

    def side_effect(_cmd: list[str], on_success: Callable[[str], None], _on_error: Any) -> None:
        on_success("Installation successful")

    run_command.side_effect = side_effect
    on_success = MagicMock()
    on_error = MagicMock()

    extension_dependencies.install(on_success, on_error)

    expected_command = [
        sys.executable,
        "-m",
        "pip",
        "install",
        "-r",
        "/fake/path/requirements.txt",
        "--target",
        "/fake/path/.dependencies",
    ]
    assert run_command.call_args.args[0] == expected_command
    on_success.assert_called_once_with("Installation successful")
    on_error.assert_not_called()


def test_install_without_requirements(
    run_command: MagicMock,
    extension_dependencies: ExtensionDependencies,
    isfile: MagicMock,
) -> None:
    isfile.return_value = False  # no requirements.txt

    on_success = MagicMock()
    on_error = MagicMock()

    extension_dependencies.install(on_success, on_error)

    run_command.assert_not_called()
    on_success.assert_called_once_with("")
    on_error.assert_not_called()


@pytest.mark.usefixtures("builtins_open")
def test_install_failure_maps_to_dependency_error(
    run_command: MagicMock,
    extension_dependencies: ExtensionDependencies,
    isfile: MagicMock,
) -> None:
    isfile.return_value = True

    def side_effect(cmd: list[str], _on_success: Any, on_error: Callable[[Exception], None]) -> None:
        on_error(subprocess.CalledProcessError(1, cmd, stderr="pip exploded"))

    run_command.side_effect = side_effect
    on_success = MagicMock()
    on_error = MagicMock()

    extension_dependencies.install(on_success, on_error)

    on_success.assert_not_called()
    on_error.assert_called_once()
    error = on_error.call_args.args[0]
    assert isinstance(error, ext_exceptions.DependencyError)
    assert "pip exploded" in str(error)
