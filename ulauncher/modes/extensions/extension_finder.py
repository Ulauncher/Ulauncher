import os

from ulauncher.config import PATHS


class ExtensionNotFound(FileNotFoundError):
    def __init__(self, ext_id):
        super().__init__(f"Extension with id {ext_id} was not found anywhere in search path")


def is_extension(ext_path):
    """
    Tells whether the argument is an extension directory
    """
    expected_files = [
        "manifest.json",
        "main.py",
    ]
    return all(os.path.isfile(os.path.join(ext_path, file)) for file in expected_files)


def is_manageable(ext_path, user_ext_path=PATHS.USER_EXTENSIONS_DIR):
    """
    Tells the directory is user-provided extension.
    """
    ext_path = os.path.realpath(ext_path)
    return os.path.dirname(ext_path) == user_ext_path and is_extension(ext_path)


def locate_iter(ext_id, exts_dirs=PATHS.ALL_EXTENSIONS_DIRS):
    """
    Yields all existing directories for given `ext_id`
    """
    for exts_dir in exts_dirs:
        ext_path = os.path.join(exts_dir, ext_id)
        if is_extension(ext_path):
            yield os.path.realpath(ext_path)


def locate(ext_id, exts_dirs=PATHS.ALL_EXTENSIONS_DIRS):
    """
    Locates (an existing) extension directory.
    """
    try:
        return next(locate_iter(ext_id, exts_dirs=exts_dirs))
    except StopIteration:
        raise ExtensionNotFound(ext_id) from None


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
