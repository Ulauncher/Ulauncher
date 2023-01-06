import os


def fold_user_path(path) -> str:
    user_dir = os.path.expanduser("~")
    if path and path.startswith(user_dir):
        return path.replace(user_dir, "~", 1)
    return path
