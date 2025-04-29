import sys
from unittest.mock import MagicMock, mock_open, patch

import pytest

from ulauncher.modes.extensions.extension_dependencies import ExtensionDependencies


@pytest.fixture
def extension_dependencies() -> ExtensionDependencies:
    return ExtensionDependencies(ext_id="extension-X", path="/fake/path")


@patch("ulauncher.modes.extensions.extension_dependencies.isfile", return_value=True)
@patch("ulauncher.modes.extensions.extension_dependencies.isdir", return_value=True)
def test_get_dependencies_path(
    mock_isdir: MagicMock, mock_isfile: MagicMock, extension_dependencies: ExtensionDependencies  # noqa: ARG001
) -> None:
    deps_path = extension_dependencies.get_dependencies_path()
    assert deps_path == "/fake/path/.dependencies"


@patch("ulauncher.modes.extensions.extension_dependencies.isfile", return_value=True)
@patch("builtins.open", new_callable=mock_open, read_data="some-package==1.0\n")
@patch("subprocess.run")
def test_install(
    mock_subprocess: MagicMock,
    mock_open_fn: MagicMock,  # noqa: ARG001
    mock_isfile: MagicMock,  # noqa: ARG001
    extension_dependencies: ExtensionDependencies,
) -> None:
    mock_subprocess.return_value = MagicMock(stdout="Installation successful", returncode=0)

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
    mock_subprocess.assert_called_once_with(expected_command, check=True, capture_output=True, text=True)
