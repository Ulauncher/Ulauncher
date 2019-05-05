import os
from fnmatch import fnmatch
from typing import Callable, Generator


def find_files(directory: str, pattern: str = None, filter_fn: Callable = None) -> Generator[str, None, None]:
    """
    Search files in `directory`
    `filter_fn` takes two arguments: directory, filename.
    If return value is False, file will be ignored
    """
    for root, _, files in os.walk(directory):
        for basename in files:
            if (not pattern or fnmatch(basename, pattern)) and (not filter_fn or filter_fn(root, basename)):
                yield os.path.join(root, basename)
