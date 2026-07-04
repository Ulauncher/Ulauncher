from types import SimpleNamespace
from unittest.mock import MagicMock, PropertyMock

import pytest
from pytest_mock import MockerFixture

from ulauncher.api.shared.event import EventType
from ulauncher.modes.extensions.extension_controller import (
    ExtensionController,
    PreviewExtensionController,
    ext_service,
)


@pytest.fixture(autouse=True)
def unclaimed_service(mocker: MockerFixture) -> None:
    mocker.patch.object(ext_service, "is_owner", False)


def test_start__raises_when_process_does_not_own_extension_runtimes() -> None:
    controller = ExtensionController("test.guard", "/nonexistent")
    with pytest.raises(RuntimeError):
        controller.start()


def test_send_message__raises_when_process_does_not_own_extension_runtimes() -> None:
    controller = ExtensionController("test.guard", "/nonexistent")
    with pytest.raises(RuntimeError):
        controller.send_message({"type": "event:unload"})


def test_preview_is_never_manageable_even_inside_user_extensions_dir(mocker: MockerFixture) -> None:
    mocker.patch("ulauncher.modes.extensions.extension_controller.extension_finder.is_manageable", return_value=True)
    preview = PreviewExtensionController("test.preview", "/nonexistent")
    assert preview.is_manageable is False


def test_save_user_preferences__saves_and_sends_changed_values(mocker: MockerFixture) -> None:
    ext = object.__new__(ExtensionController)
    ext.id = "test.ext"

    current_preferences = {
        "city": SimpleNamespace(value="Stockholm"),
        "units": SimpleNamespace(value="metric"),
    }
    mocker.patch.object(ExtensionController, "preferences", new_callable=PropertyMock, return_value=current_preferences)
    mocker.patch.object(ExtensionController, "owns_runtime", new_callable=PropertyMock, return_value=True)
    user_prefs_json = MagicMock()
    mocker.patch("ulauncher.modes.extensions.extension_controller._load_preferences", return_value=user_prefs_json)
    send_message = mocker.patch.object(ext, "send_message")

    data = {"preferences": {"city": "Berlin", "units": "metric", "undeclared": "value"}}

    ext.save_user_preferences(data)

    user_prefs_json.save.assert_called_once_with(data)
    send_message.assert_called_once_with(
        {"type": EventType.UPDATE_PREFERENCES, "args": ("city", "Berlin", "Stockholm")}
    )
