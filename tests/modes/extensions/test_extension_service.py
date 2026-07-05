from types import SimpleNamespace
from unittest.mock import MagicMock, PropertyMock

from pytest_mock import MockerFixture

from ulauncher.api.shared.event import EventType
from ulauncher.modes.extensions.extension_controller import ExtensionController, PreviewExtensionController
from ulauncher.modes.extensions.extension_service import ExtensionService


def test_preview_is_never_manageable_even_inside_user_extensions_dir(mocker: MockerFixture) -> None:
    mocker.patch("ulauncher.modes.extensions.extension_controller.extension_finder.is_manageable", return_value=True)
    preview = PreviewExtensionController("test.preview", "/nonexistent")
    assert preview.is_manageable is False


def test_save_user_preferences__saves_and_sends_changed_values(mocker: MockerFixture) -> None:
    service = object.__new__(ExtensionService)
    controller = object.__new__(ExtensionController)
    controller.id = "test.ext"

    current_preferences = {
        "city": SimpleNamespace(value="Stockholm"),
        "units": SimpleNamespace(value="metric"),
    }
    mocker.patch.object(ExtensionController, "preferences", new_callable=PropertyMock, return_value=current_preferences)
    user_prefs_json = MagicMock()
    mocker.patch("ulauncher.modes.extensions.extension_controller._load_preferences", return_value=user_prefs_json)
    send_message = mocker.patch.object(service, "send_message")

    data = {"preferences": {"city": "Berlin", "units": "metric", "undeclared": "value"}}

    service.save_user_preferences(controller, data)

    user_prefs_json.save.assert_called_once_with(data)
    send_message.assert_called_once_with(
        controller, {"type": EventType.UPDATE_PREFERENCES, "args": ("city", "Berlin", "Stockholm")}
    )
