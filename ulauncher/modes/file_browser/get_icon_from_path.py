import os
import mimetypes
from pathlib import Path
from gi.repository import GLib


SPECIAL_DIRS = {
    GLib.get_user_special_dir(GLib.UserDirectory.DIRECTORY_DOWNLOAD): "folder-download",
    GLib.get_user_special_dir(GLib.UserDirectory.DIRECTORY_DOCUMENTS): "folder-documents",
    GLib.get_user_special_dir(GLib.UserDirectory.DIRECTORY_MUSIC): "folder-music",
    GLib.get_user_special_dir(GLib.UserDirectory.DIRECTORY_PICTURES): "folder-pictures",
    GLib.get_user_special_dir(GLib.UserDirectory.DIRECTORY_PUBLIC_SHARE): "folder-publicshare",
    GLib.get_user_special_dir(GLib.UserDirectory.DIRECTORY_TEMPLATES): "folder-templates",
    GLib.get_user_special_dir(GLib.UserDirectory.DIRECTORY_VIDEOS): "folder-videos",
    GLib.get_user_special_dir(GLib.UserDirectory.DIRECTORY_DESKTOP): "user-desktop",
    Path("~").expanduser(): "folder-home",
}


def get_icon_from_path(path):
    if Path(path).is_dir():
        return SPECIAL_DIRS.get(path) or "folder"

    mime = mimetypes.guess_type(Path(path).name)[0]
    if mime:
        return mime.replace("/", "-")

    if os.access(path, os.X_OK):
        return "application-x-executable"

    return "unknown"
