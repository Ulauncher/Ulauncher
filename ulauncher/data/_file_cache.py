from __future__ import annotations

import logging
from typing import Any, TypeVar

from ulauncher.utils.json_utils import json_load_dict, json_save
from ulauncher.utils.lru_cache import lru_cache

logger = logging.getLogger(__name__)
FileInstanceT = TypeVar("FileInstanceT")
_instance_paths: dict[int, str] = {}

# Values considered "unset" defaults rather than actual data, so they're omitted from the saved file.
_EMPTY_VALUES: tuple[Any, ...] = ([], {}, None, "")


def _populate_from_file(instance: Any, file_path: str) -> None:
    try:
        data = json_load_dict(file_path)
    # Resetting to defaults would be worse than staying stale, and a save would then persist that
    except OSError:
        logger.exception("Could not read %s - keeping the cached data", file_path)
        return
    # Parse into a throwaway first, so data the class rejects raises before the cached
    # instance (which every holder of it shares) is cleared and left half-populated.
    parsed = type(instance)(data)
    instance.clear()
    instance.update(parsed)


@lru_cache(maxsize=None)
def _get_or_create_instance(cls: type[FileInstanceT], file_path: str) -> FileInstanceT:
    instance = cls()
    _instance_paths[id(instance)] = file_path
    _populate_from_file(instance, file_path)
    return instance


def _load_cached_file_instance(cls: type[FileInstanceT], path: str, *, force: bool = False) -> FileInstanceT:
    instance = _get_or_create_instance(cls, path)
    if force:
        _populate_from_file(instance, path)
    return instance


def _save_cached_file_instance(instance: object, data: Any, *, sort_keys: bool = False) -> bool:
    file_path = _instance_paths.get(id(instance))
    if file_path is None:
        logger.error("Could not resolve file path for instance %s", instance.__class__.__name__)
        return False

    return json_save(data, file_path, sort_keys=sort_keys, value_blacklist=_EMPTY_VALUES)
