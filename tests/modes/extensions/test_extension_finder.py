import os

from ulauncher.modes.extensions import extension_finder


def test_find_extensions__test_extension__is_found() -> None:
    ext_path = os.path.dirname(os.path.abspath(__file__))
    (ext_id, path) = next(iter(extension_finder.iterate([ext_path])))
    assert ext_id == "test_extension"
    assert path == f"{ext_path}/test_extension"
