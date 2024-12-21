"""
!EXPERIMENTAL: this module intends to provide an implementation of automatic
!installation and virtual environment management/setup automation of ulauncher
!extensions installed using one way or another.
"""

from pathlib import Path
from os.path import exists


def check_requirements(ext_dir: Path) -> bool:
    """check_requirements

    Args:
        ext_dir (Path): Path of the extension dir downloaded/cloned.

    Returns:
        bool: whether a requirements.txt file exists for the extension.
    """

    if exists(ext_dir / "requirements.txt"):
        return True # it should be requirements.txt only, not requirement.txt
    return False

