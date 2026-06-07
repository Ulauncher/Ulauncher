from types import SimpleNamespace
from typing import TYPE_CHECKING, Any, cast
from unittest.mock import MagicMock, PropertyMock

import pytest

if TYPE_CHECKING:
    from collections.abc import Iterator

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


@pytest.fixture
def pending_callback_setup() -> "Iterator[SimpleNamespace]":
    from ulauncher.modes.extensions import extension_mode

    mode = object.__new__(extension_mode.ExtensionMode)
    mode.active_ext = cast("Any", SimpleNamespace(id="test.ext", get_icon_value=MagicMock(return_value="icon.png")))
    mode._request_id = 1
    mode._pending_callback = MagicMock()
    extension_mode.events.set_self(mode)
    yield SimpleNamespace(mode=mode, callback=mode._pending_callback)
    extension_mode.events.set_self(None)  # the EventBus self is global state


def test_handle_response__partial_keeps_the_callback_alive(pending_callback_setup: SimpleNamespace) -> None:
    setup = pending_callback_setup

    setup.mode.handle_response("test.ext", {"request_id": 1, "partial": True, "effect": [{"name": "a"}]})

    setup.callback.assert_called_once()
    assert setup.mode._pending_callback is setup.callback

    setup.mode.handle_response("test.ext", {"request_id": 1, "effect": [{"name": "a"}, {"name": "b"}]})

    assert setup.callback.call_count == 2
    assert setup.mode._pending_callback is None


def test_handle_response__partial_flag_is_ignored_for_non_list_effects(
    pending_callback_setup: SimpleNamespace,
) -> None:
    setup = pending_callback_setup

    setup.mode.handle_response("test.ext", {"request_id": 1, "partial": True, "effect": {"type": "effect:do_nothing"}})

    setup.callback.assert_called_once()
    assert setup.mode._pending_callback is None


def test_handle_response__outdated_partial_is_ignored(pending_callback_setup: SimpleNamespace) -> None:
    setup = pending_callback_setup
    setup.mode._request_id = 2

    setup.mode.handle_response("test.ext", {"request_id": 1, "partial": True, "effect": [{"name": "a"}]})

    setup.callback.assert_not_called()
    assert setup.mode._pending_callback is setup.callback
