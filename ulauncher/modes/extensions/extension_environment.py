"""
!EXPERIMENTAL: this module intends to provide an implementation of automatic
!installation and virtual environment management/setup automation of ulauncher
!extensions installed using one way or another.
"""

from pathlib import Path
from os.path import exists


class ExtensionEnvironment:
    def __init__(self, ext_dir: Path) -> None:
        """_summary_

        Args:
            ext_dir (Path): location of the cloned/downloaded extension, usually
                this is in $HOME/.local/ulauncher/
            venv_map (dict[str, set]): _description_
        """
        self.ext_dir: Path = ext_dir

    def check_requirements(self) -> bool:
        """ Checks if the extension has a requirements.txt file.

        Returns:
            bool: Returns True if the extension contains a requirements.txt file,
                False otherwise.
        """

        if exists(self.ext_dir / "requirements.txt"):
            return True # it should be requirements.txt only, not requirement.txt
        return False

    def prep_extension(self):
        req_path: Path = self.ext_dir / "requirements.txt"

    def create_sole_venv(self):
        pass

    def install_ext(self):
        pass

