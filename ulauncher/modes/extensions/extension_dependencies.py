from __future__ import annotations

import logging
import subprocess
import sys
from os.path import isdir, isfile

logger = logging.getLogger()


class ExtensionDependenciesRecoverableError(Exception):
    pass


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

    def install(self) -> None:
        """
        Install the dependencies for the extension.
        Runs `pip install -r extension-X/requirements.txt --target extension-X/deps`
        """
        requirements = self._read_requirements()

        if not requirements:
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

        try:
            result = subprocess.run(command, check=True, capture_output=True, text=True)
            logger.info("Installation successful. Output: %s", result.stdout)
        except subprocess.CalledProcessError as e:
            logger.exception("Error during installation. Output: %s", e.stderr)

            err_msg = f"$ {command_str}\n{e.stderr}"
            raise ExtensionDependenciesRecoverableError(err_msg) from e

    def _read_requirements(self) -> str | None:
        """
        Read the requirements file and return its content.
        """
        requirements_file = f"{self.path}/requirements.txt"
        if not isfile(requirements_file):
            return None

        with open(requirements_file) as f:
            return f.read().strip()
