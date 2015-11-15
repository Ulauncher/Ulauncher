import os
from ulauncher.search.find.file_watcher import find_user_files


def test_find_user_files_ignores_hidden(tmpdir):
    "verify find_user_files exclude hidden dirs"
    dot_dir = os.path.join(str(tmpdir), '.hidden/foo')
    os.makedirs(dot_dir)
    os.system('touch %s' % os.path.join(dot_dir, 'bar.txt'))
    os.system('touch %s' % os.path.join(str(tmpdir), '.hidden/baz.txt'))

    assert list(find_user_files(dirs=[str(tmpdir)])) == []
