from __future__ import annotations

import logging
from pathlib import Path

# MutableMapping from typing (not collections.abc) supports subscript syntax on Python 3.8 for class bases.
# MutableMappingABC from collections.abc is used for isinstance checks.
from typing import Any, Callable, Generic, Iterator, MutableMapping, TypeVar, cast, get_args, get_origin

from ulauncher.utils.base_data_class import BaseDataClass
from ulauncher.utils.json_utils import json_load, json_save

logger = logging.getLogger()
T = TypeVar("T", bound="JsonConf")
V = TypeVar("V")
K = TypeVar("K", bound=str)
KVC = TypeVar("KVC", bound="JsonKeyValueConf[Any, Any]")
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


def _save_cached_file_instance(instance: object, data: Any) -> bool:
    file_path = _instance_paths.get(id(instance))
    if file_path is None:
        logger.error("Could not resolve file path for instance %s", instance.__class__.__name__)
        return False

    return json_save(data, file_path)


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


class JsonKeyValueConf(MutableMapping[str, V], Generic[K, V]):
    """File-backed mapping config for JSON objects with arbitrary string keys."""

    _value_type: type[object] | None = None

    def __init_subclass__(cls) -> None:
        super().__init_subclass__()
        if "_value_type" in cls.__dict__:
            return

        for base in getattr(cls, "__orig_bases__", ()):
            if get_origin(base) is JsonKeyValueConf:
                args = get_args(base)
                if len(args) != 2:  # noqa: PLR2004
                    msg = f"{cls.__name__}: JsonKeyValueConf requires exactly 2 type args, got {len(args)}"
                    raise TypeError(msg)
                # `is str` is intentional: we're checking type identity, not equality.
                # The builtin `str` type object is a singleton, so `is` is correct here.
                if args[0] is not str:
                    msg = f"{cls.__name__}: key type must be str, got {args[0]!r}"
                    raise TypeError(msg)
                if not isinstance(args[1], type):
                    msg = f"{cls.__name__}: value type must be a concrete type, got {args[1]!r}"
                    raise TypeError(msg)
                cls._value_type = args[1]
                return

        if cls._value_type is None:
            msg = f"{cls.__name__} must be declared as JsonKeyValueConf[str, <concrete type>]"
            raise TypeError(msg)

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self._data: dict[str, V] = {}
        self.update(*args, **kwargs)

    def __getitem__(self, key: str) -> V:
        return self._data[key]

    def _coerce_value(self, value: Any) -> V:
        value_type = self._value_type
        if value_type is None or isinstance(value, value_type):
            return cast("V", value)
        coercer = cast("Callable[[Any], V]", value_type)
        return coercer(value)

    def __setitem__(self, key: str, value: Any) -> None:
        # None is treated as a delete signal rather than stored, matching the pattern used in
        # the preferences UI where setting a key to None removes it from the config.
        if value is None:
            self._data.pop(key, None)
            return
        self._data[key] = self._coerce_value(value)

    def __delitem__(self, key: str) -> None:
        del self._data[key]

    def __iter__(self) -> Iterator[str]:
        return iter(self._data)

    def __len__(self) -> int:
        return len(self._data)

    def __repr__(self) -> str:
        return repr(self._data)

    @classmethod
    def load(cls: type[KVC], path: str | Path) -> KVC:
        instance, data = _load_cached_file_instance(cls, path)
        if isinstance(data, dict):
            instance.clear()
            instance.update(data)
        elif data is not None:
            logger.warning("Expected a JSON object in %s, got %s — file ignored", path, type(data).__name__)
        return instance

    def save(self, *args: Any, **kwargs: Any) -> bool:
        self.update(*args, **kwargs)
        return _save_cached_file_instance(self, dict(self.items()))
