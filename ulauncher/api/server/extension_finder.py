import os


def find_extensions(ext_dir):
    """
    Yields `(extension_id, extension_path)` tuples found in a given extensions dir
    """
    if not os.path.exists(ext_dir):
        return

    dirs = [d for d in os.listdir(ext_dir) if os.path.isdir(os.path.join(ext_dir, d))]
    for dir in dirs:
        ext_path = os.path.join(ext_dir, dir)
        if os.path.isfile(os.path.join(ext_path, 'manifest.json')):
            yield (dir, ext_path)
