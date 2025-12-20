import signal
from typing import Any
from unittest.mock import MagicMock, Mock

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
    def message_socket(self, mocker: MockerFixture) -> MagicMock:
        mock_parent_sock = Mock()
        mock_child_sock = Mock()
        mock_child_sock.fileno.return_value = 1
        mock_parent_sock.fileno.return_value = 2
        return mocker.patch(
            "ulauncher.modes.extensions.extension_runtime.socket.socketpair",
            return_value=(mock_parent_sock, mock_child_sock),
        )

    @pytest.fixture(autouse=True)
    def message_socket_class(self, mocker: MockerFixture) -> MagicMock:
        return mocker.patch("ulauncher.modes.extensions.extension_runtime.SocketMsgController")

    @pytest.fixture
    def time(self, mocker: MockerFixture) -> MagicMock:
        return mocker.patch("ulauncher.modes.extensions.extension_runtime.time")

    @pytest.fixture
    def mock_timer(self, mocker: MockerFixture) -> MagicMock:
        """Mock the timer utility function used for scheduling delayed kills."""
        return mocker.patch("ulauncher.modes.extensions.extension_runtime.timer")

    def test_run__basic_execution__is_called(self, subprocess_launcher: MagicMock) -> None:
        extid = "mock.test_run__basic_execution__is_called"

        runtime: Any = ExtensionRuntime(extid, ["mock/path/to/ext"])

        subprocess_launcher.new.assert_called_once()
        runtime._subprocess.wait_async.assert_called_once()
        runtime._error_stream.read_line_async.assert_called_once()

    def test_read_stderr_line(self) -> None:
        test_output1 = "Test Output 1"
        test_output2 = "Test Output 2"
        extid = "mock.test_read_stderr_line"
        mock_read_line_finish_utf8 = Mock()

        runtime: Any = ExtensionRuntime(extid, ["mock/path/to/ext"])
        runtime._error_stream.read_line_finish_utf8 = mock_read_line_finish_utf8

        mock_read_line_finish_utf8.return_value = (test_output1, len(test_output1))
        runtime.handle_stderr(runtime._error_stream, Mock())
        # Confirm the output is stored in recent_errors and read_line_async is called for the next
        # line.
        assert runtime._recent_errors[0] == test_output1
        assert runtime._error_stream.read_line_async.call_count == 2

        mock_read_line_finish_utf8.return_value = (test_output2, len(test_output2))
        runtime.handle_stderr(runtime._error_stream, Mock())
        # The latest line should replace the previous line
        assert runtime._recent_errors[0] == test_output2
        assert runtime._error_stream.read_line_async.call_count == 3

    def test_handle_exit__signaled(self) -> None:
        extid = "mock.test_handle_exit__signaled"
        exit_handler = Mock()

        runtime = ExtensionRuntime(extid, ["mock/path/to/ext"], None, exit_handler)
        aborted_subprocesses.add(runtime._subprocess)

        runtime.handle_exit(runtime._subprocess, Mock())
        exit_handler.assert_called_once_with("Stopped", "Extension was stopped by the user")

    def test_handle_exit__rapid_exit(self, time: MagicMock) -> None:
        extid = "mock.test_handle_exit__rapid_exit"
        curtime = 100.0
        starttime = curtime - 0.5
        time.return_value = starttime
        exit_handler = Mock()

        runtime: Any = ExtensionRuntime(extid, ["mock/path/to/ext"], None, exit_handler)
        runtime._subprocess.get_if_signaled.return_value = False
        runtime._subprocess.get_exit_status.return_value = 9
        time.return_value = curtime

        runtime.handle_exit(runtime._subprocess, Mock())
        exit_handler.assert_called()

    def test_handle_exit(self, time: MagicMock) -> None:
        extid = "mock.test_handle_exit"
        exit_handler = Mock()
        curtime = 100.0
        starttime = curtime - 5
        time.return_value = starttime

        runtime: Any = ExtensionRuntime(extid, ["mock/path/to/ext"], None, exit_handler)
        runtime._subprocess.get_if_signaled.return_value = False
        runtime._subprocess.get_exit_status.return_value = 9
        time.return_value = curtime
        runtime.handle_exit(runtime._subprocess, Mock())
        exit_handler.assert_called_once_with(
            "Exited", 'Extension "mock.test_handle_exit" exited with code 9 after 5.0 seconds.'
        )

    def test_stop(self, mock_timer: MagicMock) -> None:
        """Test that stop() closes the connection and schedules a kill timer."""
        extid = "mock.test_stop"
        exit_handler = Mock()
        runtime: Any = ExtensionRuntime(extid, ["mock/path/to/ext"], None, exit_handler)

        runtime._subprocess.get_exit_status.return_value = None
        runtime._msg_controller = Mock()
        runtime.stop()

        runtime._msg_controller.close.assert_called_once()
        mock_timer.assert_called_once_with(0.5, runtime._kill)

    def test_kill__sends_sigkill(self) -> None:
        """Test that _kill() sends SIGKILL if the process is still running."""

        extid = "mock.test_kill__sends_sigkill"
        runtime: Any = ExtensionRuntime(extid, ["mock/path/to/ext"])

        # Simulate process still running
        runtime._subprocess.get_exit_status.return_value = None
        runtime._kill()

        # Verify SIGKILL is sent
        runtime._subprocess.send_signal.assert_called_once_with(signal.SIGKILL)
