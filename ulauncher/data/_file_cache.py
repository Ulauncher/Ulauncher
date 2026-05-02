from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, TypeVar, cast

from ulauncher.utils.json_utils import json_load, json_save

logger = logging.getLogger()
FileInstanceT = TypeVar("FileInstanceT")
_file_instances: dict[tuple[Path, type[object]], object] = {}
_instance_paths: dict[int, Path] = {}


def _load_cached_file_instance(cls: type[FileInstanceT], path: str | Path) -> tuple[FileInstanceT, Any]:
    file_path = Path(path).resolve()
    key = (file_path, cls)
    data = json_load(file_path)
    instance = cast("FileInstanceT", _file_instances.get(key))
    if instance is None:
        instance = cls()
        _file_instances[key] = instance
        _instance_paths[id(instance)] = file_path
    return instance, data


def _save_cached_file_instance(instance: object, data: Any, *, sort_keys: bool = True) -> bool:
    file_path = _instance_paths.get(id(instance))
    if file_path is None:
        logger.error("Could not resolve file path for instance %s", instance.__class__.__name__)
        return False

    return json_save(data, file_path, sort_keys=sort_keys)
