import os

from ulauncher.config import PATHS


def is_extension(directory):
    """
    Tells whether the argument is an extension directory
    """
    manifest = os.path.join(directory, "manifest.json")
    manifest = os.path.realpath(manifest)
    return os.path.isfile(manifest)


def locate(ext_id, ext_dirs=PATHS.EXTENSIONS_ALL_DIRS):
    """
    Locates (an existing) extension directory.
    """
    for ext_dir in ext_dirs:
        ext_path = os.path.join(ext_dir, ext_id)
        if is_extension(ext_path):
            return os.path.realpath(ext_path)
    return None


def get_mutable_dir(ext_id, mutable_ext_dir=PATHS.EXTENSIONS_WRITE_DIR):
    """
    Returns path to writable extension directory
    """
    return os.path.realpath(os.path.join(mutable_ext_dir, ext_id))


def iterate(ext_dirs=PATHS.EXTENSIONS_ALL_DIRS, duplicates=False):
    """
    Yields `(extension_id, extension_path)` tuples found in a given extensions dirs
    """
    occurrences = set()
    for ext_dir in ext_dirs:
        if not os.path.exists(ext_dir):
            continue
        for entry in os.scandir(ext_dir):
            if is_extension(entry.path) and (duplicates or entry.name not in occurrences):
                occurrences.add(entry.name)
                yield entry.name, os.path.realpath(entry.path)
