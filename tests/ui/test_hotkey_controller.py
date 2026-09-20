from __future__ import annotations

import time
from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture

from ulauncher.ui.helpers.hotkey_controller import LEAK_SWALLOW_SECONDS, HotkeyController


@pytest.fixture(autouse=True)
def _reset_portal_state() -> None:
    """show_config() reads class-level portal state that must not leak between tests."""
    HotkeyController._portal = None


def test_show_config__opens_the_portals_config_ui(mocker: MockerFixture) -> None:
    portal = mocker.Mock()
    portal.configure.return_value = True
    HotkeyController._portal = portal
    launch_detached = mocker.patch("ulauncher.ui.helpers.hotkey_controller.launch_detached")

    assert HotkeyController.show_config() is True
    launch_detached.assert_not_called()


@pytest.mark.parametrize(
    ("desktop_id", "expected_cmd"),
    [
        ("GNOME", ["gnome-control-center", "applications", "io.ulauncher.Ulauncher"]),
        ("PLASMA", ["systemsettings5", "kcm_keys"]),
    ],
)
def test_show_config__falls_back_to_de_settings_without_portal_v2(
    mocker: MockerFixture, desktop_id: str, expected_cmd: list[str]
) -> None:
    mocker.patch("ulauncher.ui.helpers.hotkey_controller.DESKTOP_ID", desktop_id)
    # Only the newer binary exists, as on current distro releases
    mocker.patch(
        "ulauncher.ui.helpers.hotkey_controller.which",
        side_effect=lambda alias: "/usr/bin/systemsettings5" if alias == "systemsettings5" else None,
    )
    launch_detached = mocker.patch("ulauncher.ui.helpers.hotkey_controller.launch_detached")

    assert HotkeyController.show_config() is True
    launch_detached.assert_called_once_with(expected_cmd)


def test_show_config__unknown_desktop_has_no_fallback(mocker: MockerFixture) -> None:
    mocker.patch("ulauncher.ui.helpers.hotkey_controller.DESKTOP_ID", "LXQT")
    launch_detached = mocker.patch("ulauncher.ui.helpers.hotkey_controller.launch_detached")

    assert HotkeyController.show_config() is False
    launch_detached.assert_not_called()


def set_trigger(description: str, activated_at: float | None = 0.0) -> MagicMock:
    portal = MagicMock()
    portal.trigger_description = description
    portal.activated_at = activated_at
    HotkeyController._portal = portal
    return portal


def fake_event(keyval: int) -> MagicMock:
    return MagicMock(keyval=keyval)


@pytest.mark.parametrize(
    ("description", "expected_keyval"),
    [
        ("Press <Control><Alt>space", 32),  # GNOME 50 format
        ("<Control>space", 32),  # our preferred_trigger echoed back
        ("Ctrl+Alt+Space", 32),  # KDE style isn't GTK accelerator syntax
        ("Press <Primary>k", ord("k")),
        ("Press <Control>Return", 65293),
    ],
)
def test_trigger_keyval__parses_de_trigger_formats(description: str, expected_keyval: int) -> None:
    set_trigger(description)
    assert HotkeyController.trigger_keyval() == expected_keyval


def test_trigger_keyval__unparsable_description_returns_none() -> None:
    set_trigger("Nothing useful here")
    assert HotkeyController.trigger_keyval() is None


def test_trigger_keyval__none_without_portal() -> None:
    assert HotkeyController.trigger_keyval() is None


def test_current_trigger_label__uses_the_de_text_without_the_press_instruction() -> None:
    set_trigger("Press <Control><Alt>space")
    assert HotkeyController.current_trigger_label() == "<Control><Alt>space"

    set_trigger("Ctrl+Space")
    assert HotkeyController.current_trigger_label() == "Ctrl+Space"


def test_current_trigger_label__falls_back_to_the_preferred_trigger() -> None:
    assert HotkeyController.current_trigger_label() == "Ctrl+Space"


def test_swallow_leaked_trigger__eats_the_trigger_key_after_activation(mocker: MockerFixture) -> None:
    now = time.monotonic()
    mocker.patch("ulauncher.ui.helpers.hotkey_controller.time.monotonic", return_value=now + 0.1)
    set_trigger("Press <Control>space", activated_at=now)

    assert HotkeyController.swallow_leaked_trigger(fake_event(32)) is True


def test_swallow_leaked_trigger__ends_when_another_key_arrives(mocker: MockerFixture) -> None:
    now = time.monotonic()
    mocker.patch("ulauncher.ui.helpers.hotkey_controller.time.monotonic", return_value=now + 0.1)
    portal = set_trigger("Press <Control>space", activated_at=now)

    assert HotkeyController.swallow_leaked_trigger(fake_event(107)) is False
    # state is cleared, so the same trigger key now passes through
    assert portal.activated_at is None
    assert HotkeyController.swallow_leaked_trigger(fake_event(32)) is False


def test_swallow_leaked_trigger__expires(mocker: MockerFixture) -> None:
    now = time.monotonic()
    mocker.patch("ulauncher.ui.helpers.hotkey_controller.time.monotonic", return_value=now + LEAK_SWALLOW_SECONDS + 0.1)
    set_trigger("Press <Control>space", activated_at=now)

    assert HotkeyController.swallow_leaked_trigger(fake_event(32)) is False


def test_swallow_leaked_trigger__inactive_without_portal_or_trigger() -> None:
    event = fake_event(32)
    assert HotkeyController.swallow_leaked_trigger(event) is False

    set_trigger("Press <Control>space", activated_at=None)
    assert HotkeyController.swallow_leaked_trigger(event) is False

    set_trigger("", activated_at=0.0)
    assert HotkeyController.swallow_leaked_trigger(event) is False
