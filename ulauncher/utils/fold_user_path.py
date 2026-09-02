import os


def fold_user_path(path: str) -> str:
    user_dir = os.path.expanduser("~")
    if not path or not user_dir:
        return path
    if path == user_dir:
        return "~"
    if path.startswith(user_dir + os.sep):
        return "~" + path[len(user_dir) :]
    return path
