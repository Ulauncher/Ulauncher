import os

from ulauncher import paths
from ulauncher.modes.extensions import extension_finder


def test_find_extensions__test_extension__is_found() -> None:
    ext_path = os.path.dirname(os.path.abspath(__file__))
    (ext_id, path) = next(iter(extension_finder.iterate([ext_path])))
    assert ext_id == "test_extension"
    assert path == f"{ext_path}/test_extension"


def test_scratch_dirs__are_outside_every_scanned_dir() -> None:
    for scratch_dir in (paths.EXTENSIONS_STAGING, paths.REPO_CACHE):
        for scanned_dir in paths.ALL_EXTENSIONS_DIRS:
            assert not scratch_dir.startswith(f"{scanned_dir}{os.sep}")
