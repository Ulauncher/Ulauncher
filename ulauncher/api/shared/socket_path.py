import os.path
from xdg.BaseDirectory import get_runtime_dir


def get_socket_path():
    """Gets the path to the Ulauncher control unix socket."""
    try:
        rundir = get_runtime_dir()
    except KeyError:
        rundir = "/tmp"
    return os.path.join(rundir, "ulauncher_control")
