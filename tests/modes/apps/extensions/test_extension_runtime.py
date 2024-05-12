import asyncio
import signal
from unittest import mock

import pytest

from ulauncher.modes.extensions.extension_runtime import ExtensionRuntime


class TestExtensionRuntime:
    @pytest.fixture(autouse=True)
    def subprocess_launcher(self, mocker):
        return mocker.patch("ulauncher.modes.extensions.extension_runtime.Gio.SubprocessLauncher")

    @pytest.fixture(autouse=True)
    def data_input_stream(self, mocker):
        return mocker.patch("ulauncher.modes.extensions.extension_runtime.Gio.DataInputStream")

    @pytest.fixture
    def time(self, mocker):
        return mocker.patch("ulauncher.modes.extensions.extension_runtime.time")

    def test_run__basic_execution__is_called(self, subprocess_launcher):
        extid = "mock.test_run__basic_execution__is_called"

        runtime = ExtensionRuntime(extid, ["mock/path/to/ext"])

        subprocess_launcher.new.assert_called_once()
        runtime.subprocess.wait_async.assert_called_once()
        runtime.error_stream.read_line_async.assert_called_once()

    def test_read_stderr_line(self):
        test_output1 = "Test Output 1"
        test_output2 = "Test Output 2"
        extid = "mock.test_read_stderr_line"
        mock_read_line_finish_utf8 = mock.Mock()

        runtime = ExtensionRuntime(extid, ["mock/path/to/ext"])
        runtime.error_stream.read_line_finish_utf8 = mock_read_line_finish_utf8

        mock_read_line_finish_utf8.return_value = (test_output1, len(test_output1))
        runtime.handle_stderr(runtime.error_stream, mock.Mock())
        # Confirm the output is stored in recent_errors and read_line_async is called for the next
        # line.
        assert runtime.recent_errors[0] == test_output1
        assert runtime.error_stream.read_line_async.call_count == 2

        mock_read_line_finish_utf8.return_value = (test_output2, len(test_output2))
        runtime.handle_stderr(runtime.error_stream, mock.Mock())
        # The latest line should replace the previous line
        assert runtime.recent_errors[0] == test_output2
        assert runtime.error_stream.read_line_async.call_count == 3

    def test_handle_exit__signaled(self):
        extid = "mock.test_handle_exit__signaled"
        err_cb = mock.Mock()

        runtime = ExtensionRuntime(extid, ["mock/path/to/ext"], None, err_cb)
        runtime.subprocess.get_if_signaled.return_value = True
        runtime.subprocess.get_term_sig.return_value = 9
        # Check pre-condition
        err_cb.assert_not_called()

        runtime.handle_exit(runtime.subprocess, mock.Mock())
        # Confirm error handling
        err_cb.assert_called_once_with(
            "Terminated", 'Extension "mock.test_handle_exit__signaled" was terminated with signal 9'
        )

    def test_handle_exit__rapid_exit(self, time):
        extid = "mock.test_handle_exit__rapid_exit"
        curtime = 100.0
        starttime = curtime - 0.5
        time.return_value = starttime
        err_cb = mock.Mock()

        runtime = ExtensionRuntime(extid, ["mock/path/to/ext"], None, err_cb)
        runtime.subprocess.get_if_signaled.return_value = False
        runtime.subprocess.get_exit_status.return_value = 9
        time.return_value = curtime

        runtime.handle_exit(runtime.subprocess, mock.Mock())
        err_cb.assert_called()

    def test_handle_exit(self, time):
        extid = "mock.test_handle_exit"
        err_cb = mock.Mock()
        curtime = 100.0
        starttime = curtime - 5
        time.return_value = starttime

        runtime = ExtensionRuntime(extid, ["mock/path/to/ext"], None, err_cb)
        runtime.subprocess.get_if_signaled.return_value = False
        runtime.subprocess.get_exit_status.return_value = 9
        time.return_value = curtime
        runtime.handle_exit(runtime.subprocess, mock.Mock())
        err_cb.assert_called_once_with(
            "Exited", 'Extension "mock.test_handle_exit" exited with code 9 after 5.0 seconds.'
        )

    def test_stop(self):
        extid = "mock.test_stop"
        err_cb = mock.Mock()
        runtime = ExtensionRuntime(extid, ["mock/path/to/ext"], None, err_cb)

        runtime.subprocess.get_identifier.return_value = None
        asyncio.run(runtime.stop())
        runtime.subprocess.send_signal.assert_called_with(signal.SIGTERM)

        runtime.subprocess.get_identifier.return_value = "ID"
        asyncio.run(runtime.stop())
        runtime.subprocess.send_signal.assert_called_with(signal.SIGKILL)
