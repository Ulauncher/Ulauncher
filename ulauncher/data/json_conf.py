from __future__ import annotations

from pathlib import Path
from typing import Any, TypeVar

from ulauncher.data._file_cache import _load_cached_file_instance, _save_cached_file_instance
from ulauncher.data.base_data_class import BaseDataClass

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
        instance, data = _load_cached_file_instance(cls, path)
        instance.update(data)
        return instance

    def save(self, *args: Any, **kwargs: Any) -> bool:
        self.update(*args, **kwargs)
        return _save_cached_file_instance(self, self)
