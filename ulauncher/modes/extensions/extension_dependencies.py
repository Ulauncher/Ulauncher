from __future__ import annotations

import logging
import sys
from os.path import isdir, isfile

from ulauncher.modes.extensions import ext_exceptions
from ulauncher.utils.subprocess_utils import OnError, OnSuccess, run_command

logger = logging.getLogger(__name__)


class ExtensionDependencies:
    """
    Manages python dependencies of the extension.
    """

    ext_id: str
    path: str

    deps_out_subdir: str = ".dependencies"

    def __init__(self, ext_id: str, path: str) -> None:
        self.ext_id = ext_id
        self.path = path

    def get_dependencies_path(self) -> str | None:
        """
        Get the path to the dependencies directory.
        Returns None if there's no dependencies for the extension.
        """
        requirements_file = f"{self.path}/requirements.txt"
        deps_path = f"{self.path}/{self.deps_out_subdir}"
        if not isfile(requirements_file) or not isdir(deps_path):
            return None

        return deps_path

    def install(self, on_success: OnSuccess, on_error: OnError) -> None:
        """
        Install the dependencies for the extension, without blocking.
        Runs `pip install -r extension-X/requirements.txt --target extension-X/.dependencies`.
        Calls on_success(stdout) when finished (including when there's nothing to install), or
        on_error(DependencyError) if pip fails.
        """
        try:
            requirements = self._read_requirements()
        except OSError as e:
            on_error(ext_exceptions.DependencyError(f"Could not read {self.path}/requirements.txt: {e}"))
            return

        if not requirements:
            on_success("")
            return

        command = [
            sys.executable,
            "-m",
            "pip",
            "install",
            "-r",
            f"{self.path}/requirements.txt",
            "--target",
            f"{self.path}/{self.deps_out_subdir}",
        ]
        command_str = " ".join(command)
        logger.info("Installing dependencies for %s. Running: %s", self.ext_id, command_str)

        def on_installed(stdout: str) -> None:
            logger.info("Installation successful. Output: %s", stdout)
            on_success(stdout)

        def on_failed(error: Exception) -> None:
            # run_command reports a non-zero pip exit as CalledProcessError, whose stderr/stdout hold the diagnostics
            output = getattr(error, "stderr", None) or getattr(error, "output", None) or str(error)
            logger.error("Error during installation. Output: %s", output, exc_info=error)
            on_error(ext_exceptions.DependencyError(f"$ {command_str}\n{output}"))

        run_command(command, on_installed, on_failed)

    def _read_requirements(self) -> str | None:
        """
        Read the requirements file and return its content.
        """
        requirements_file = f"{self.path}/requirements.txt"
        if not isfile(requirements_file):
            return None

        with open(requirements_file) as f:
            return f.read().strip()
