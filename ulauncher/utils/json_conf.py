from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, TypeVar, cast

from ulauncher.utils.basedataclass import BaseDataClass
from ulauncher.utils.json_utils import json_load, json_save

# See https://stackoverflow.com/a/63237226/633921 for why JsonConf is quoted
_file_instances: dict[tuple[Path, type], JsonConf] = {}
logger = logging.getLogger()
T = TypeVar("T", bound="JsonConf")


class JsonConf(BaseDataClass):
    """
    JsonConf

    This is an helper class to handle json config files
    It has two convenient methods for loading and saving the data, which also depuplicate class instances,
    So that if you create two instances for the same file it will actually reuse the first instance
    (to avoid overwriting state changes)

    File paths are stored in an external reference object, which is not part of the data.
    """

    @classmethod
    def load(cls: type[T], path) -> T:
        data = {}
        file_path = Path(path).resolve()
        key = (file_path, cls)
        if key not in _file_instances:
            data = json_load(file_path)

        instance = _file_instances.get(key, cls())
        instance.update(data)
        _file_instances[key] = instance
        return cast(T, instance)

    def save(self, sort_keys=True, indent=2, value_blacklist: list[Any] | None = None) -> bool:
        file_path = next((key[0] for key, inst in _file_instances.items() if inst == self), None)

        return json_save(self, file_path, sort_keys, indent, value_blacklist)
