from __future__ import annotations

import subprocess
from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture

from ulauncher.data import Err, Ok
from ulauncher.utils.systemd_controller import SystemdController, SystemdUnitStatus
from ulauncher.utils.systemd_controller import systemctl_run as run_systemctl


@pytest.fixture
def systemctl_run(mocker: MockerFixture) -> MagicMock:
    return mocker.patch("ulauncher.utils.systemd_controller.systemctl_run")


@pytest.fixture
def controller(mocker: MockerFixture) -> SystemdController:
    mocker.patch("ulauncher.utils.systemd_controller.which", return_value="/usr/bin/systemctl")
    return SystemdController("ulauncher")


class TestSystemctlRun:
    def test_err_falls_back_to_exit_code_when_output_is_empty(self, mocker: MockerFixture) -> None:
        error = subprocess.CalledProcessError(3, ["systemctl", "--user", "show", "ulauncher"])
        mocker.patch("ulauncher.utils.systemd_controller.subprocess.run", side_effect=error)
        result = run_systemctl("show", "ulauncher")
        assert isinstance(result, Err)
        assert result.error == "exit code 3"


class TestSystemdUnitStatus:
    def test_reads_properties(self) -> None:
        status = SystemdUnitStatus(["ActiveState=active", "CanStart=yes", "UnitFileState=enabled"])
        assert status.is_active
        assert status.can_start
        assert status.is_enabled


class TestSystemdController:
    def test_status_returns_parsed_output(self, controller: SystemdController, systemctl_run: MagicMock) -> None:
        systemctl_run.return_value = Ok("ActiveState=active\nCanStart=yes")
        result = controller.status()
        assert isinstance(result, Ok)
        assert result.value.is_active
        assert result.value.can_start

    def test_status_returns_err_when_show_fails(self, controller: SystemdController, systemctl_run: MagicMock) -> None:
        systemctl_run.return_value = Err("dbus down")
        result = controller.status()
        assert isinstance(result, Err)
        assert result.error == "dbus down"

    def test_status_reloads_daemon_before_retrying(
        self, controller: SystemdController, systemctl_run: MagicMock
    ) -> None:
        systemctl_run.side_effect = [Ok("NeedDaemonReload=yes"), Ok(""), Ok("ActiveState=active")]
        result = controller.status()
        assert isinstance(result, Ok)
        assert result.value.is_active
        assert [call.args for call in systemctl_run.call_args_list] == [
            ("show", "ulauncher"),
            ("daemon-reload",),
            ("show", "ulauncher"),
        ]

    def test_status_returns_err_when_retry_fails(self, controller: SystemdController, systemctl_run: MagicMock) -> None:
        systemctl_run.side_effect = [Ok("NeedDaemonReload=yes"), Ok(""), Err("boom")]
        result = controller.status()
        assert isinstance(result, Err)
        assert result.error == "boom"

    def test_status_returns_err_when_reload_fails(
        self, controller: SystemdController, systemctl_run: MagicMock
    ) -> None:
        systemctl_run.side_effect = [Ok("NeedDaemonReload=yes"), Err("reload failed")]
        result = controller.status()
        assert isinstance(result, Err)
        assert result.error == "reload failed"
        assert len(systemctl_run.call_args_list) == 2

    def test_status_without_systemctl_is_ok(self, mocker: MockerFixture) -> None:
        mocker.patch("ulauncher.utils.systemd_controller.which", return_value=None)
        result = SystemdController("ulauncher").status()
        assert isinstance(result, Ok)
        assert not result.value.is_active

    def test_toggle_enables(self, controller: SystemdController, systemctl_run: MagicMock) -> None:
        systemctl_run.return_value = Ok("CanStart=yes")
        controller.toggle(True)
        assert [call.args for call in systemctl_run.call_args_list] == [
            ("show", "ulauncher"),
            ("reenable", "ulauncher"),
        ]

    def test_toggle_raises_when_status_query_fails(
        self, controller: SystemdController, systemctl_run: MagicMock
    ) -> None:
        systemctl_run.return_value = Err("dbus down")
        with pytest.raises(OSError, match="dbus down"):
            controller.toggle(True)

    def test_toggle_raises_when_unit_cannot_start(
        self, controller: SystemdController, systemctl_run: MagicMock
    ) -> None:
        systemctl_run.return_value = Ok("CanStart=no")
        with pytest.raises(OSError, match="Autostart is not allowed"):
            controller.toggle(True)

    def test_toggle_disables_without_querying(self, controller: SystemdController, systemctl_run: MagicMock) -> None:
        controller.toggle(False)
        systemctl_run.assert_called_once_with("disable", "ulauncher")
