from types import SimpleNamespace
from unittest.mock import MagicMock, PropertyMock

from pytest_mock import MockerFixture

from ulauncher.api.shared.event import EventType
from ulauncher.modes.extensions import extension_registry
from ulauncher.modes.extensions.extension_controller import ExtensionController
from ulauncher.modes.extensions.extension_controller import events as controller_events


def test_save_user_preferences__emits_old_preferences(mocker: MockerFixture) -> None:
    controller = object.__new__(ExtensionController)
    controller.id = "test.ext"

    current_preferences = {"city": SimpleNamespace(value="Stockholm")}
    mocker.patch.object(ExtensionController, "preferences", new_callable=PropertyMock, return_value=current_preferences)

    user_prefs_json = MagicMock()
    mocker.patch("ulauncher.modes.extensions.extension_controller._load_preferences", return_value=user_prefs_json)
    emit = mocker.patch.object(controller_events, "emit")

    data = {"preferences": {"city": "Berlin"}}

    controller.save_user_preferences(data)

    user_prefs_json.save.assert_called_once_with(data)
    emit.assert_called_once_with(
        "extensions:update_preferences",
        "test.ext",
        {"preferences": {"city": "Berlin"}, "old_preferences": {"city": "Stockholm"}},
    )


def test_update_preferences__uses_emitted_old_preferences(mocker: MockerFixture) -> None:
    from ulauncher.modes.extensions import extension_mode

    ext = SimpleNamespace(
        preferences={"city": SimpleNamespace(value="Berlin")},
        send_message=MagicMock(),
    )
    mocker.patch.object(extension_registry, "get", return_value=ext)

    mode = object.__new__(extension_mode.ExtensionMode)
    mode._trigger_cache = {}
    extension_mode.events.set_self(mode)
    mode.update_preferences(
        "test.ext",
        {
            "preferences": {"city": "Berlin"},
            "old_preferences": {"city": "Stockholm"},
        },
    )

    ext.send_message.assert_called_once_with(
        {"type": EventType.UPDATE_PREFERENCES, "args": ["city", "Berlin", "Stockholm"]}
    )
