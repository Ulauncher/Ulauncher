import subprocess
from typing import List


def trigger_action(method: str, arguments: List[str]):
    # fmt: off
    # pylint: disable=consider-using-with
    subprocess.Popen([
        "gdbus",
        "call", "--session",
        "--dest", "io.ulauncher.Ulauncher",
        "--object-path", "/io/ulauncher/Ulauncher",
        "--method", f"io.ulauncher.Ulauncher.actions.{method}",
    ] + arguments or [])
