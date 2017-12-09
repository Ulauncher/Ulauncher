import logging
import os
import sys
from subprocess import Popen
from time import time, sleep

from ulauncher.config import EXTENSIONS_DIR, ULAUNCHER_APP_DIR, get_options
from ulauncher.util.decorator.run_async import run_async
from ulauncher.util.decorator.singleton import singleton
from .ExtensionManifest import ExtensionManifest
from .ExtensionServer import ExtensionServer
from .extension_finder import find_extensions

logger = logging.getLogger(__name__)


class ExtensionRunner(object):

    @classmethod
    @singleton
    def get_instance(cls):
        return cls(ExtensionServer.get_instance())

    def __init__(self, extension_server):
        self.extensions_dir = EXTENSIONS_DIR
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
            except Exception as e:
                logger.error("Couldn't run '%s'. %s: %s" % (id, type(e).__name__, e.message))

    def run(self, extension_id):
        """
        * Validates manifest
        * Runs extension in a new process

        :rtype: :class:`threading.Thread`
        """
        if self.is_running(extension_id):
            raise ExtensionIsRunningError('Extension ID: %s' % extension_id)

        manifest = ExtensionManifest.open(extension_id)
        manifest.check_compatibility()
        manifest.validate()

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
            logger.warning('Copy and run the following command to start %s' % extension_id)
            logger.warning('VERBOSE=%s ULAUNCHER_WS_API=%s PYTHONPATH=%s %s %s' % tuple(args))
            return

        while True:
            t_start = time()
            proc = Popen(cmd, env=env)
            logger.info('Extension "%s" started. PID %s' % (extension_id, proc.pid))
            self.extension_procs[extension_id] = proc
            code = proc.wait()

            if code <= 0:
                logger.error('Extension "%s" was terminated with code %s' % (extension_id, code))
                try:
                    del self.extension_procs[extension_id]
                except KeyError:
                    pass

                break

            if time() - t_start < 1:
                logger.error('Extension "%s" exited instantly with code %s' % (extension_id, code))
                try:
                    del self.extension_procs[extension_id]
                except KeyError:
                    pass

                break

            logger.error('Extension "%s" exited with code %s. Restarting...' % (extension_id, code))

    def stop(self, extension_id):
        """
        Terminates extension
        """
        if not self.is_running(extension_id):
            raise ExtensionIsNotRunningError('Extension ID: %s' % extension_id)

        logger.info('Terminating extension "%s"' % extension_id)
        proc = self.extension_procs[extension_id]
        try:
            del self.extension_procs[extension_id]
        except KeyError:
            pass

        terminate = run_async(proc.terminate)
        terminate()

        sleep(0.5)
        if proc.poll() is None:
            logger.warn("Kill extension \"%s\" since it doesn't react to SIGTERM" % extension_id)
            proc.kill()

    def is_running(self, extension_id):
        return extension_id in self.extension_procs.keys()


class ExtensionIsRunningError(RuntimeError):
    pass


class ExtensionIsNotRunningError(RuntimeError):
    pass


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)

    runner = ExtensionRunner()
    runner.extensions_dir = '/home/agornostal/projects/ulauncher/tests/extension/server'
    runner.run('test_extension')
    sleep(1.5)
    runner.stop('test_extension')
    print(runner.is_running('test_extension'))
