import logging
import os
import sys
from subprocess import Popen, PIPE
from typing import Dict, Optional
from time import time, sleep
from enum import Enum

from ulauncher.config import EXTENSIONS_DIR, ULAUNCHER_APP_DIR, get_options
from ulauncher.utils.decorator.run_async import run_async
from ulauncher.utils.mypy_extensions import TypedDict
from ulauncher.utils.decorator.singleton import singleton
from ulauncher.api.server.ExtensionManifest import ExtensionManifest
from ulauncher.api.server.ExtensionServer import ExtensionServer
from ulauncher.api.server.ProcessErrorExtractor import ProcessErrorExtractor
from ulauncher.api.server.extension_finder import find_extensions

logger = logging.getLogger(__name__)

ExtRunError = TypedDict('ExtRunError', {
    'name': str,
    'message': str
})


class ExtRunErrorName(Enum):
    NoExtensionsFlag = 'NoExtensionsFlag'
    Terminated = 'Terminated'
    Exited = 'Exited'
    MissingModule = 'MissingModule'


class ExtensionRunner:

    @classmethod
    @singleton
    def get_instance(cls) -> 'ExtensionRunner':
        return cls(ExtensionServer.get_instance())

    def __init__(self, extension_server):
        self.extensions_dir = EXTENSIONS_DIR
        self.extension_errors: Dict[str, ExtRunError] = {}
        self.extension_procs = {}
        self.extension_server = extension_server
        self.dont_run_extensions = get_options().no_extensions
        self.verbose = get_options().verbose

    def run_all(self):
        """
        Finds all extensions in `EXTENSIONS_DIR` and runs them
        """
        for id, _ in find_extensions(self.extensions_dir):
            try:
                self.run(id)
            # pylint: disable=broad-except
            except Exception as e:
                logger.error("Couldn't run '%s'. %s: %s", id, type(e).__name__, e)

    def run(self, extension_id):
        """
        * Validates manifest
        * Runs extension in a new process

        :rtype: :class:`threading.Thread`
        """
        if self.is_running(extension_id):
            raise ExtensionIsRunningError('Extension ID: %s' % extension_id)

        manifest = ExtensionManifest.open(extension_id)
        manifest.validate()
        manifest.check_compatibility()

        run_process = run_async(daemon=True)(self._run_process)
        run_process(extension_id)

    def _run_process(self, extension_id):
        """
        Blocking function
        """
        cmd = [sys.executable, os.path.join(self.extensions_dir, extension_id, 'main.py')]
        env = os.environ.copy()
        env['ULAUNCHER_WS_API'] = self.extension_server.generate_ws_url(extension_id)
        env['PYTHONPATH'] = ':'.join(filter(bool, [ULAUNCHER_APP_DIR, os.getenv('PYTHONPATH')]))

        if self.verbose:
            env['VERBOSE'] = '1'

        if self.dont_run_extensions:
            args = [env.get('VERBOSE', ''), env['ULAUNCHER_WS_API'], env['PYTHONPATH']]
            args.extend(cmd)
            run_cmd = 'VERBOSE={} ULAUNCHER_WS_API={} PYTHONPATH={} {} {}'.format(*args)
            logger.warning('Copy and run the following command to start %s', extension_id)
            logger.warning(run_cmd)
            self.set_extension_error(extension_id, ExtRunErrorName.NoExtensionsFlag, run_cmd)

            return

        while True:
            t_start = time()
            proc = Popen(cmd, env=env, stderr=PIPE)
            lasterr = ""
            logger.info('Extension "%s" started. PID %s', extension_id, proc.pid)
            self.unset_extension_error(extension_id)

            while proc.poll() is None:
                line = proc.stderr.readline().decode()
                if line != "":
                    lasterr = line
                    print(line, end='')

            code = proc.returncode

            if code == 0:
                self.extension_procs[extension_id] = proc
            else:
                error_msg = 'Extension "%s" was terminated with code %s' % (extension_id, code)
                logger.error(error_msg)
                self.set_extension_error(extension_id, ExtRunErrorName.Terminated, error_msg)
                break

            if time() - t_start < 1:
                error_msg = 'Extension "%s" exited instantly with code %s' % (extension_id, code)
                logger.error(error_msg)
                self.set_extension_error(extension_id, ExtRunErrorName.Terminated, error_msg)
                error_info = ProcessErrorExtractor(lasterr)
                logger.error('Extension "%s" failed with an error: %s', extension_id, error_info.error)
                if error_info.is_import_error():
                    self.set_extension_error(extension_id, ExtRunErrorName.MissingModule,
                                             error_info.get_missing_package_name())

                try:
                    del self.extension_procs[extension_id]
                except KeyError:
                    pass

                break

            error_msg = 'Extension "%s" exited with code %s. Restarting...' % (extension_id, code)
            self.set_extension_error(extension_id, ExtRunErrorName.Exited, error_msg)
            logger.error(error_msg)

    def stop(self, extension_id):
        """
        Terminates extension
        """
        if not self.is_running(extension_id):
            raise ExtensionIsNotRunningError('Extension ID: %s' % extension_id)

        logger.info('Terminating extension "%s"', extension_id)
        proc = self.extension_procs[extension_id]
        try:
            del self.extension_procs[extension_id]
        except KeyError:
            pass

        terminate = run_async(proc.terminate)
        terminate()

        sleep(0.5)
        if proc.poll() is None:
            logger.warning("Kill extension \"%s\" since it doesn't react to SIGTERM", extension_id)
            proc.kill()

    def is_running(self, extension_id: str) -> bool:
        return extension_id in self.extension_procs.keys()

    def set_extension_error(self, extension_id: str, errorName: ExtRunErrorName, message: str):
        self.extension_errors[extension_id] = {
            'name': errorName.value,
            'message': message
        }

    def unset_extension_error(self, extension_id: str):
        try:
            del self.extension_errors[extension_id]
        except KeyError:
            pass

    def get_extension_error(self, extension_id: str) -> Optional[ExtRunError]:
        return self.extension_errors.get(extension_id)


class ExtensionIsRunningError(RuntimeError):
    pass


class ExtensionIsNotRunningError(RuntimeError):
    pass
