from unittest.mock import MagicMock, call

import pytest
from pytest_mock import MockerFixture

from ulauncher.utils import dbus


@pytest.fixture
def gio(mocker: MockerFixture) -> MagicMock:
    return mocker.patch("ulauncher.utils.dbus.Gio")


@pytest.fixture
def action_group(mocker: MockerFixture) -> MagicMock:
    return mocker.patch("ulauncher.utils.dbus.get_ulauncher_dbus_action_group").return_value


class TestDbusTriggerEvent:
    def test_flushes_the_bus_after_activating_the_action(
        self, gio: MagicMock, action_group: MagicMock, mocker: MockerFixture
    ) -> None:
        mocker.patch("ulauncher.utils.dbus.check_app_running", return_value=True)
        bus = gio.bus_get_sync.return_value

        # flush must follow activate so the queued message is on the socket before the process exits
        parent = MagicMock()
        parent.attach_mock(action_group.activate_action, "activate")
        parent.attach_mock(bus.flush_sync, "flush")

        dbus.dbus_trigger_event("extensions:stop_preview")

        assert parent.mock_calls == [call.activate("trigger-event", mocker.ANY), call.flush(None)]

    def test_does_nothing_when_app_is_not_running(
        self, gio: MagicMock, action_group: MagicMock, mocker: MockerFixture
    ) -> None:
        mocker.patch("ulauncher.utils.dbus.check_app_running", return_value=False)

        dbus.dbus_trigger_event("extensions:stop_preview")

        action_group.activate_action.assert_not_called()
        gio.bus_get_sync.return_value.flush_sync.assert_not_called()
