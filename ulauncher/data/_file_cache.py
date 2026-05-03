from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, MutableMapping, TypeVar, cast

from ulauncher.utils.json_utils import json_load, json_save
from ulauncher.utils.lru_cache import lru_cache

logger = logging.getLogger()
FileInstanceT = TypeVar("FileInstanceT")
_MappingT = TypeVar("_MappingT", bound="MutableMapping[str, Any]")
_instance_paths: dict[int, Path] = {}


@lru_cache(maxsize=None)
def _get_or_create_instance(cls: type[FileInstanceT], file_path: Path) -> FileInstanceT:
    instance = cls()
    _instance_paths[id(instance)] = file_path
    return cast("FileInstanceT", instance)


def _load_cached_file_instance(cls: type[_MappingT], path: str) -> _MappingT:
    file_path = Path(path).resolve()
    data = json_load(file_path)
    instance = _get_or_create_instance(cls, file_path)
    if isinstance(data, dict):
        instance.clear()
        instance.update(data)
    elif data is not None:
        logger.warning("Expected a JSON object in %s, got %s — file ignored", file_path, type(data).__name__)
    return instance


def _save_cached_file_instance(instance: object, data: Any, *, sort_keys: bool = False) -> bool:
    file_path = _instance_paths.get(id(instance))
    if file_path is None:
        logger.error("Could not resolve file path for instance %s", instance.__class__.__name__)
        return False

    return json_save(data, file_path, sort_keys=sort_keys)
