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

    def __setitem__(self, key: str, value: dict[str, Any], validate_type: bool = True) -> None:
        if hasattr(self.__class__, key):
            class_val = getattr(self.__class__, key)
            # WARNING: this logic does not work with union types or nullable types,
            # since it derives the type from the initial class value
            if validate_type and not isinstance(value, type(class_val)):
                msg = f'"{key}" must be of type {type(class_val).__name__}, {type(value).__name__} given.'
                raise KeyError(msg)

        super().__setitem__(key, value)

    @classmethod
    def load(cls: type[T], path: str | Path) -> T:
        data = {}
        file_path = Path(path).resolve()
        key = (file_path, cls)
        data = json_load(file_path)

        instance = _file_instances.get(key, cls())
        instance.update(data)
        _file_instances[key] = instance
        return cast("T", instance)

    def save(self, *args: Any, **kwargs: Any) -> bool:
        self.update(*args, **kwargs)
        file_path = next((key[0] for key, inst in _file_instances.items() if inst == self), None)
        assert file_path

        return json_save(self, file_path)
