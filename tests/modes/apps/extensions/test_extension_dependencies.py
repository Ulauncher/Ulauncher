import sys
from typing import Any, Callable
from unittest.mock import MagicMock, mock_open

import pytest
from pytest_mock import MockerFixture

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
def subprocess_run(mocker: MockerFixture) -> MagicMock:
    return mocker.patch("subprocess.run")


@pytest.mark.usefixtures("isfile", "isdir")
def test_get_dependencies_path(
    extension_dependencies: ExtensionDependencies,
) -> None:
    deps_path = extension_dependencies.get_dependencies_path()
    assert deps_path == "/fake/path/.dependencies"


@pytest.mark.usefixtures("builtins_open")
def test_install(
    subprocess_run: MagicMock,
    extension_dependencies: ExtensionDependencies,
    isfile: MagicMock,
) -> None:
    isfile.return_value = True
    subprocess_run.return_value = MagicMock(stdout="Installation successful", returncode=0)

    extension_dependencies.install()

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
    subprocess_run.assert_called_once_with(expected_command, check=True, capture_output=True, text=True)
