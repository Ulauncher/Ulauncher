import logging
import os
import sys
import signal
from collections import namedtuple, deque
from functools import partial
from typing import Dict, Optional
from time import time
from enum import Enum

import gi

gi.require_versions({
    "Gio": "2.0",
    "GLib": "2.0",
})
# pylint: disable=wrong-import-position
from gi.repository import Gio, GLib

from ulauncher.config import EXTENSIONS_DIR, ULAUNCHER_APP_DIR, get_options
from ulauncher.utils.mypy_extensions import TypedDict
from ulauncher.utils.decorator.singleton import singleton
from ulauncher.utils.timer import timer
from ulauncher.modes.extensions.ExtensionManifest import ExtensionManifest
from ulauncher.modes.extensions.ExtensionServer import ExtensionServer
from ulauncher.modes.extensions.ProcessErrorExtractor import ProcessErrorExtractor
from ulauncher.modes.extensions.extension_finder import find_extensions

logger = logging.getLogger(__name__)

ExtRunError = TypedDict('ExtRunError', {
    'name': str,
    'message': str
})

ExtensionProc = namedtuple("ExtensionProc", (
    "extension_id", "subprocess", "start_time", "error_stream", "recent_errors"
))


class ExtRunErrorName(Enum):
    NoExtensionsFlag = 'NoExtensionsFlag'
    Terminated = 'Terminated'
    ExitedInstantly = 'ExitedInstantly'
    Exited = 'Exited'
    MissingModule = 'MissingModule'
    Incompatible = 'Incompatible'


class ExtensionRunner:

    @classmethod
    @singleton
    def get_instance(cls) -> 'ExtensionRunner':
        return cls(ExtensionServer.get_instance())

    def __init__(self, extension_server):
        self.extensions_dir = EXTENSIONS_DIR  # type: str
        self.extension_errors = {}  # type: Dict[str, ExtRunError]
        self.extension_procs = {}
        self.extension_server = extension_server
        self.dont_run_extensions = get_options().no_extensions
        self.verbose = get_options().verbose

    def run_all(self):
        """
        Finds all extensions in `EXTENSIONS_DIR` and runs them
        """
        for ex_id, _ in find_extensions(self.extensions_dir):
            try:
                self.run(ex_id)
            # pylint: disable=broad-except
            except Exception as e:
                logger.error("Couldn't run '%s'. %s: %s", ex_id, type(e).__name__, e)

    def run(self, extension_id):
        """
        * Validates manifest
        * Runs extension in a new process
        """
        if self.is_running(extension_id):
            raise ExtensionIsRunningError(f"Extension ID: {extension_id}")

        manifest = ExtensionManifest.open(extension_id)
        manifest.validate()
        manifest.check_compatibility()

        cmd = ['pip-run', '--'] if manifest.get_use_pip_run() else [sys.executable]
        cmd.extend([os.path.join(self.extensions_dir, extension_id, 'main.py')])

        env = {}
        env['PYTHONPATH'] = ':'.join(filter(bool, [ULAUNCHER_APP_DIR, os.getenv('PYTHONPATH')]))

        if self.verbose:
            env['VERBOSE'] = '1'

        if self.dont_run_extensions:
            args = [env.get('VERBOSE', ''), env['PYTHONPATH']]
            args.extend(cmd)
            run_cmd = 'VERBOSE={} PYTHONPATH={} {} {}'.format(*args)
            logger.warning('Copy and run the following command to start %s', extension_id)
            logger.warning(run_cmd)
            self.set_extension_error(extension_id, ExtRunErrorName.NoExtensionsFlag, run_cmd)
            return

        launcher = Gio.SubprocessLauncher.new(Gio.SubprocessFlags.STDERR_PIPE)
        for env_name, env_value in env.items():
            launcher.setenv(env_name, env_value, True)

        t_start = time()
        subproc = launcher.spawnv(cmd)
        error_line_str = Gio.DataInputStream.new(subproc.get_stderr_pipe())
        self.extension_procs[extension_id] = ExtensionProc(
            extension_id=extension_id,
            subprocess=subproc,
            start_time=t_start,
            error_stream=error_line_str,
            recent_errors=deque(maxlen=1)
        )
        logger.debug("Launched %s using Gio.Subprocess", extension_id)

        subproc.wait_async(None, self.handle_wait, extension_id)
        self.read_stderr_line(self.extension_procs[extension_id])

    def read_stderr_line(self, extproc):
        extproc.error_stream.read_line_async(
            GLib.PRIORITY_DEFAULT,
            None,
            self.handle_stderr,
            extproc.extension_id
        )

    def handle_stderr(self, error_stream, result, extension_id):
        output, _ = error_stream.read_line_finish(result)
        if output:
            print(output.decode())
        extproc = self.extension_procs.get(extension_id)
        if not extproc:
            logger.debug("Extension process context for %s no longer present", extension_id)
            return
        if output:
            extproc.recent_errors.append(output)
        self.read_stderr_line(extproc)

    def handle_wait(self, subprocess, result, extension_id):
        subprocess.wait_finish(result)
        if subprocess.get_if_signaled():
            code = subprocess.get_term_sig()
            error_msg = f'Extension "{extension_id}" was terminated with code {code}'
            logger.error(error_msg)
            self.set_extension_error(extension_id, ExtRunErrorName.Terminated, error_msg)
            self.extension_procs.pop(extension_id, None)
            return

        extproc = self.extension_procs.get(extension_id)
        if not extproc or id(extproc.subprocess) != id(subprocess):
            logger.info("Exited process %s for %s has already been removed. Not restarting.", subprocess, extension_id)
            return

        runtime = time() - extproc.start_time
        code = subprocess.get_exit_status()
        if runtime < 1:
            error_msg = f'Extension "{extension_id}" exited instantly with code {code}'
            logger.error(error_msg)
            self.set_extension_error(extension_id, ExtRunErrorName.ExitedInstantly, error_msg)
            lasterr = b"\n".join(extproc.recent_errors).decode()
            error_info = ProcessErrorExtractor(lasterr)
            logger.error('Extension "%s" failed with an error: %s', extension_id, error_info.error)
            if error_info.is_import_error():
                package_name = error_info.get_missing_package_name()
                if package_name == "ulauncher":
                    logger.error('Extension tried to import Ulauncher modules which have been moved or removed. '
                                 'This is likely Ulauncher internals which were not part of the extension API. '
                                 'Extensions importing these can break at any Ulauncher release.')
                    self.set_extension_error(extension_id, ExtRunErrorName.Incompatible, error_msg)
                elif package_name:
                    self.set_extension_error(extension_id, ExtRunErrorName.MissingModule, package_name)

            self.extension_procs.pop(extension_id, None)
            return

        error_msg = f'Extension "{extension_id}" exited with code {code} after {runtime} seconds. Restarting...'
        self.set_extension_error(extension_id, ExtRunErrorName.Exited, error_msg)
        logger.error(error_msg)
        self.extension_procs.pop(extension_id, None)
        self.run(extension_id)

    def stop(self, extension_id):
        """
        Terminates extension
        """
        if not self.is_running(extension_id):
            raise ExtensionIsNotRunningError(f"Extension ID: {extension_id}")

        logger.info('Terminating extension "%s"', extension_id)
        extproc = self.extension_procs[extension_id]
        self.extension_procs.pop(extension_id, None)

        extproc.subprocess.send_signal(signal.SIGTERM)

        timer(0.5, partial(self.confirm_termination, extproc))

    def confirm_termination(self, extproc):
        if extproc.subprocess.get_identifier():
            logger.info("Extension %s still running, sending SIGKILL", extproc.extension_id)
            # It is possible that the process exited between the check above and this signal,
            # luckily the subprocess library handles the signal delivery in race-free way, so this
            # is safe to do.
            extproc.subprocess.send_signal(signal.SIGKILL)

    def is_running(self, extension_id: str) -> bool:
        return extension_id in self.extension_procs

    def set_extension_error(self, extension_id: str, errorName: ExtRunErrorName, message: str):
        self.extension_errors[extension_id] = {
            'name': errorName.value,
            'message': message
        }

    def get_extension_error(self, extension_id: str) -> Optional[ExtRunError]:
        return self.extension_errors.get(extension_id)


class ExtensionIsRunningError(RuntimeError):
    pass


class ExtensionIsNotRunningError(RuntimeError):
    pass
