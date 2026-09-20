from __future__ import annotations

import pytest
from pytest_mock import MockerFixture

from ulauncher.ui.helpers.hotkey_controller import HotkeyController


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
        ("GNOME", ["gnome-control-center", "keyboard"]),
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
