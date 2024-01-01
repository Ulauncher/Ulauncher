import signal
from unittest import mock

import pytest

from ulauncher.modes.extensions.ExtensionRunner import ExtensionRunner


class TestExtensionRunner:
    @pytest.fixture
    def runner(self):
        return ExtensionRunner()

    @pytest.fixture(autouse=True)
    def timer(self, mocker):
        return mocker.patch("ulauncher.modes.extensions.ExtensionRunner.timer")

    @pytest.fixture(autouse=True)
    def SubprocessLauncher(self, mocker):
        return mocker.patch("ulauncher.modes.extensions.ExtensionRunner.Gio.SubprocessLauncher")

    @pytest.fixture(autouse=True)
    def DataInputStream(self, mocker):
        return mocker.patch("ulauncher.modes.extensions.ExtensionRunner.Gio.DataInputStream")

    @pytest.fixture
    def time(self, mocker):
        return mocker.patch("ulauncher.modes.extensions.ExtensionRunner.time")

    def test_run__basic_execution__is_called(self, runner, SubprocessLauncher):
        extid = "id"
        runner.run(extid, "path")
        SubprocessLauncher.new.assert_called_once()
        extproc = runner.extension_procs[extid]
        extproc.subprocess.wait_async.assert_called_once()
        extproc.error_stream.read_line_async.assert_called_once()

    def test_read_stderr_line(self, runner):
        test_output1 = "Test Output 1"
        test_output2 = "Test Output 2"
        extid = "id"
        read_line_finish_utf8 = mock.Mock()

        runner.run(extid, "path")
        extproc = runner.extension_procs[extid]
        extproc.error_stream.read_line_finish_utf8 = read_line_finish_utf8

        read_line_finish_utf8.return_value = (test_output1, len(test_output1))
        runner.handle_stderr(extproc.error_stream, mock.Mock(), extid)
        # Confirm the output is stored in recent_errors and read_line_async is called for the next
        # line.
        assert extproc.recent_errors[0] == test_output1
        assert extproc.error_stream.read_line_async.call_count == 2

        read_line_finish_utf8.return_value = (test_output2, len(test_output2))
        runner.handle_stderr(extproc.error_stream, mock.Mock(), extid)
        # The latest line should replace the previous line
        assert extproc.recent_errors[0] == test_output2
        assert extproc.error_stream.read_line_async.call_count == 3

    def test_handle_exit__signaled(self, runner):
        extid = "id"
        err_cb = mock.Mock()

        runner.run(extid, "path", {}, err_cb)
        extproc = runner.extension_procs[extid]
        extproc.subprocess.get_if_signaled.return_value = True
        extproc.subprocess.get_term_sig.return_value = 9
        # Check pre-condition
        err_cb.assert_not_called()

        runner.handle_exit(extproc.subprocess, mock.Mock(), extid)
        # Confirm error handling
        err_cb.assert_called_once_with("Terminated", 'Extension "id" was terminated with signal 9')
        assert extid not in runner.extension_procs

    def test_handle_exit__rapid_exit(self, runner, time):
        extid = "id"
        curtime = 100.0
        starttime = curtime - 0.5
        time.return_value = starttime
        err_cb = mock.Mock()

        runner.run(extid, "path", {}, err_cb)
        extproc = runner.extension_procs[extid]
        extproc.subprocess.get_if_signaled.return_value = False
        extproc.subprocess.get_exit_status.return_value = 9
        time.return_value = curtime

        runner.handle_exit(extproc.subprocess, mock.Mock(), extid)
        err_cb.assert_called()
        assert extid not in runner.extension_procs

    def test_handle_exit(self, runner, time):
        extid = "id"
        curtime = 100.0
        starttime = curtime - 5
        time.return_value = starttime
        err_cb = mock.Mock()

        runner.run(extid, "path", {}, err_cb)
        extproc = runner.extension_procs[extid]
        extproc.subprocess.get_if_signaled.return_value = False
        extproc.subprocess.get_exit_status.return_value = 9
        time.return_value = curtime

        runner.run = mock.Mock()
        runner.handle_exit(extproc.subprocess, mock.Mock(), extid)
        err_cb.assert_called_once_with("Exited", 'Extension "id" exited with code 9 after 5.0 seconds.')
        assert extid not in runner.extension_procs

    def test_stop(self, runner, timer):
        extid = "id"

        runner.run(extid, "path")
        extproc = runner.extension_procs[extid]
        runner.stop(extid)
        assert extid not in runner.extension_procs
        extproc.subprocess.send_signal.assert_called_with(signal.SIGTERM)
        timer.assert_called_once()

    def test_confirm_termination(self, runner):
        extproc = mock.Mock()
        extproc.subprocess.get_identifier.return_value = None

        runner.confirm_termination(extproc)
        extproc.subprocess.send_signal.assert_not_called()

        extproc.subprocess.get_identifier.return_value = 1
        runner.confirm_termination(extproc)
        extproc.subprocess.send_signal.assert_called_with(signal.SIGKILL)
