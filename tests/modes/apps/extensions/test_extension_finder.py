import os

from ulauncher.modes.extensions import extension_finder


def test_find_extensions__test_extension__is_found():
    ext_dir = os.path.dirname(os.path.abspath(__file__))
    (id, path) = next(iter(extension_finder.iterate([ext_dir])))
    assert id == "test_extension"
    assert path == f"{ext_dir}/test_extension"
