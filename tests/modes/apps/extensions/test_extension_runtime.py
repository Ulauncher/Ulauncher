import asyncio
import signal
from typing import Any
from unittest.mock import MagicMock, Mock, call

import pytest
from pytest_mock import MockerFixture

from ulauncher.modes.extensions.extension_runtime import ExtensionRuntime, aborted_subprocesses


class TestExtensionRuntime:
    @pytest.fixture(autouse=True)
    def subprocess_launcher(self, mocker: MockerFixture) -> MagicMock:
        return mocker.patch("ulauncher.modes.extensions.extension_runtime.Gio.SubprocessLauncher")

    @pytest.fixture(autouse=True)
    def data_input_stream(self, mocker: MockerFixture) -> MagicMock:
        return mocker.patch("ulauncher.modes.extensions.extension_runtime.Gio.DataInputStream")

    @pytest.fixture(autouse=True)
    def data_output_stream(self, mocker: MockerFixture) -> MagicMock:
        return mocker.patch("ulauncher.modes.extensions.extension_runtime.Gio.DataOutputStream")

    @pytest.fixture
    def time(self, mocker: MockerFixture) -> MagicMock:
        return mocker.patch("ulauncher.modes.extensions.extension_runtime.time")

    def test_run__basic_execution__is_called(self, subprocess_launcher: MagicMock) -> None:
        extid = "mock.test_run__basic_execution__is_called"

        runtime: Any = ExtensionRuntime(extid, ["mock/path/to/ext"])

        subprocess_launcher.new.assert_called_once()
        runtime.subprocess.wait_async.assert_called_once()
        runtime.stderr.read_line_async.assert_called_once()

    def test_read_stderr_line(self) -> None:
        test_output1 = "Test Output 1"
        test_output2 = "Test Output 2"
        extid = "mock.test_read_stderr_line"
        mock_read_line_finish_utf8 = Mock()

        runtime: Any = ExtensionRuntime(extid, ["mock/path/to/ext"])
        runtime.stderr.read_line_finish_utf8 = mock_read_line_finish_utf8

        mock_read_line_finish_utf8.return_value = (test_output1, len(test_output1))
        runtime.handle_stderr(runtime.stderr, Mock())
        # Confirm the output is stored in recent_errors and read_line_async is called for the next
        # line.
        assert runtime.recent_errors[0] == test_output1
        assert runtime.stderr.read_line_async.call_count == 2

        mock_read_line_finish_utf8.return_value = (test_output2, len(test_output2))
        runtime.handle_stderr(runtime.stderr, Mock())
        # The latest line should replace the previous line
        assert runtime.recent_errors[0] == test_output2
        assert runtime.stderr.read_line_async.call_count == 3

    def test_handle_exit__signaled(self) -> None:
        extid = "mock.test_handle_exit__signaled"
        exit_handler = Mock()

        runtime = ExtensionRuntime(extid, ["mock/path/to/ext"], None, exit_handler)
        aborted_subprocesses.add(runtime.subprocess)

        runtime.handle_exit(runtime.subprocess, Mock())
        exit_handler.assert_not_called()

    def test_handle_exit__rapid_exit(self, time: MagicMock) -> None:
        extid = "mock.test_handle_exit__rapid_exit"
        curtime = 100.0
        starttime = curtime - 0.5
        time.return_value = starttime
        exit_handler = Mock()

        runtime: Any = ExtensionRuntime(extid, ["mock/path/to/ext"], None, exit_handler)
        runtime.subprocess.get_if_signaled.return_value = False
        runtime.subprocess.get_exit_status.return_value = 9
        time.return_value = curtime

        runtime.handle_exit(runtime.subprocess, Mock())
        exit_handler.assert_called()

    def test_handle_exit(self, time: MagicMock) -> None:
        extid = "mock.test_handle_exit"
        exit_handler = Mock()
        curtime = 100.0
        starttime = curtime - 5
        time.return_value = starttime

        runtime: Any = ExtensionRuntime(extid, ["mock/path/to/ext"], None, exit_handler)
        runtime.subprocess.get_if_signaled.return_value = False
        runtime.subprocess.get_exit_status.return_value = 9
        time.return_value = curtime
        runtime.handle_exit(runtime.subprocess, Mock())
        exit_handler.assert_called_once_with(
            "Exited", 'Extension "mock.test_handle_exit" exited with code 9 after 5.0 seconds.'
        )

    def test_stop_noop_if_not_running(self) -> None:
        extid = "mock.test_stop_noop_if_not_running"
        exit_handler = Mock()
        runtime: Any = ExtensionRuntime(extid, ["mock/path/to/ext"], None, exit_handler)

        runtime.subprocess.get_identifier.return_value = None
        asyncio.run(runtime.stop())
        runtime.subprocess.send_signal.assert_not_called()

    def test_stop(self) -> None:
        extid = "mock.test_stop"
        exit_handler = Mock()
        runtime: Any = ExtensionRuntime(extid, ["mock/path/to/ext"], None, exit_handler)

        runtime.subprocess.get_identifier.return_value = "ID"
        asyncio.run(runtime.stop())
        runtime.subprocess.send_signal.assert_has_calls([call(signal.SIGTERM), call(signal.SIGKILL)])
