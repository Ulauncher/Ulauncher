from types import SimpleNamespace
from unittest.mock import MagicMock, PropertyMock

from pytest_mock import MockerFixture

from ulauncher.modes.extensions.extension_controller import ExtensionController


def test_start__advertises_partial_responses_capability(mocker: MockerFixture) -> None:
    """Without this env flag extensions silently stop streaming (see api/extension.py)."""
    controller = object.__new__(ExtensionController)
    controller.id = "test.ext"
    controller.path = "/tmp/test.ext"
    controller.state = MagicMock()
    controller.shadowed_by_preview = False
    controller.manifest = MagicMock(triggers={})

    mocker.patch.object(ExtensionController, "is_running", new_callable=PropertyMock, return_value=False)
    mocker.patch.object(ExtensionController, "preferences", new_callable=PropertyMock, return_value={})
    deps = mocker.patch("ulauncher.modes.extensions.extension_controller.ExtensionDependencies")
    deps.return_value.get_dependencies_path.return_value = ""
    mocker.patch(
        "ulauncher.modes.extensions.extension_controller.cli.get_args",
        return_value=SimpleNamespace(verbose=False),
    )
    runtime = mocker.patch("ulauncher.modes.extensions.extension_controller.ExtensionRuntime")

    controller.start()  # returns is_running, which is mocked — the spawn env is what matters here

    env = runtime.call_args.args[2]
    assert env["ULAUNCHER_PARTIAL_RESPONSES"] == "1"
