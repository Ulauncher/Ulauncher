import os
from fnmatch import fnmatch


def find_files(directory, pattern=None, filter_fn=None):
    """
    Search files in `directory`
    `filter_fn` takes two arguments: directory, filename.
    If return value is False, file will be ignored
    """
    for root, _, files in os.walk(directory):
        for basename in files:
            if (not pattern or fnmatch(basename, pattern)) and (not filter_fn or filter_fn(root, basename)):
                yield os.path.join(root, basename)
