from __future__ import annotations

import logging
from typing import Any, TypeVar, cast

from ulauncher.utils.json_utils import json_load, json_save
from ulauncher.utils.lru_cache import lru_cache

logger = logging.getLogger()
FileInstanceT = TypeVar("FileInstanceT")
_instance_paths: dict[int, str] = {}


def _populate_from_file(instance: Any, file_path: str) -> None:
    data = json_load(file_path)
    if isinstance(data, dict):
        instance.clear()
        instance.update(data)
    elif data is None:
        logger.warning("File not found or unreadable: %s — keeping cached data", file_path)
    else:
        logger.warning("Expected a JSON object in %s, got %s — file ignored", file_path, type(data).__name__)


@lru_cache(maxsize=None)
def _get_or_create_instance(cls: type[FileInstanceT], file_path: str) -> FileInstanceT:
    instance = cls()
    _instance_paths[id(instance)] = file_path
    _populate_from_file(instance, file_path)
    return cast("FileInstanceT", instance)


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

    return json_save(data, file_path, sort_keys=sort_keys)
