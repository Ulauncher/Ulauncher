"""
!EXPERIMENTAL: this module intends to provide an implementation of automatic
!installation and virtual environment management/setup automation of ulauncher
!extensions installed using one way or another.
"""

from pathlib import Path
from os.path import exists


class ExtensionEnvironment:
    def __init__(self, ext_dir: Path, venv_map: dict[str, set]) -> None:
        self.ext_dir: Path = ext_dir
        self.venv_map: dict[str, set[str]] = {
            "test": set(
                    [
                        "hello==1.0" # this is for testing purposes
                    ]
                )
        }

#     def check_requirements(self) -> bool:
#         """check_requirements
#
#         Args:
#             ext_dir (Path): Path of the extension dir downloaded/cloned.
#
#         Returns:
#             bool: whether a requirements.txt file exists for the extension.
#         """
#
#         if exists(self.ext_dir / "requirements.txt"):
#             return True # it should be requirements.txt only, not requirement.txt
#         return False

    def prep_extension(self):
        req_path: Path = self.ext_dir / "requirements.txt"

        if not self.check_requirements():
            self.create_sole_venv()

        with open(req_path, "r", encoding="utf-8") as req_file:
            dependencies: set[str] = set(req_file.readlines())

        for venv in self.venv_map.keys():
            if dependencies >= self.venv_map.get(venv): # type: ignore
                self.create_sole_venv()
            else:
                continue

            self.install_ext(venv)

    def create_sole_venv(self):
        pass

    def install_ext(self):
        pass

