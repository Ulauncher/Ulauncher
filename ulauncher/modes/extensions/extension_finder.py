import os

from ulauncher.config import PATHS


def is_extension(ext_path):
    """
    Tells whether the argument is an extension directory
    """
    expected_files = [
        "manifest.json",
        "main.py",
    ]
    return all(os.path.isfile(os.path.join(ext_path, file)) for file in expected_files)




def locate(ext_id, exts_dirs=PATHS.ALL_EXTENSIONS_DIRS):
    """
    Locates (an existing) extension directory.
    """
    for exts_dir in exts_dirs:
        ext_path = os.path.join(exts_dir, ext_id)
        if is_extension(ext_path):
            return os.path.realpath(ext_path)
    return None


def get_user_dir(ext_id, user_ext_path=PATHS.USER_EXTENSIONS_DIR):
    """
    Returns path to writable extension directory
    """
    return os.path.realpath(os.path.join(user_ext_path, ext_id))


def iterate(exts_dirs=PATHS.ALL_EXTENSIONS_DIRS, duplicates=False):
    """
    Yields `(extension_id, extension_path)` tuples found in a given extensions dirs
    """
    occurrences = set()
    for ext_path in exts_dirs:
        if not os.path.exists(ext_path):
            continue
        for entry in os.scandir(ext_path):
            ext_id = entry.name
            if is_extension(entry.path) and (duplicates or ext_id not in occurrences):
                occurrences.add(ext_id)
                yield ext_id, os.path.realpath(entry.path)
