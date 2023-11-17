import os


def is_extension(directory):
    """
    Tells whether the argument is an extension directory
    """
    manifest = os.path.join(directory, "manifest.json")
    manifest = os.path.realpath(manifest)
    return os.path.isfile(manifest)


def locate_extension(ext_id, ext_dirs, default=None, default_first=False):
    ret = default
    for ext_dir in ext_dirs:
        ext_path = os.path.join(ext_dir, ext_id)
        if default_first and ret is None:
            ret = ext_path
        elif is_extension(ext_path):
            ret = ext_path
            break
    if ret:
        ret = os.path.realpath(ret)
    return ret


def iter_extensions(ext_dirs, duplicates=False):
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
