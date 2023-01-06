from pathlib import Path
from ulauncher.utils.fold_user_path import fold_user_path


def test_fold_user_path():
    assert fold_user_path(str(Path("/bin").expanduser())) == "/bin"
    assert fold_user_path(str(Path("/usr/bin/foo").expanduser())) == "/usr/bin/foo"
    relative_path = str(Path("~/foo/bar//").expanduser())
    assert relative_path != "~/foo/bar"
    assert fold_user_path(relative_path) == "~/foo/bar"
