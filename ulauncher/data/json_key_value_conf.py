from __future__ import annotations

# MutableMapping from typing (not collections.abc) supports subscript syntax on Python 3.8 for class bases.
from typing import Any, Callable, Generic, Iterator, MutableMapping, TypeVar, cast, get_args, get_origin

from ulauncher.data._file_cache import _get_or_create_instance, _reload_file_instance, _save_cached_file_instance

V = TypeVar("V")
K = TypeVar("K", bound=str)
KVC = TypeVar("KVC", bound="JsonKeyValueConf[Any, Any]")


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
                key_type, value_type = args
                # `is str` is intentional: we're checking type identity, not equality.
                # The builtin `str` type object is a singleton, so `is` is correct here.
                if key_type is not str:
                    msg = f"{cls.__name__}: key type must be str, got {key_type!r}"
                    raise TypeError(msg)
                if value_type in (str, int, float, bool):
                    return  # no coercion needed
                if value_type in (list, dict):
                    msg = (
                        f"{cls.__name__}: unparameterized {value_type} not supported. "
                        f"Use list[...] for lists and BaseDataClass subclasses or dict[K, V] for dicts"
                    )
                    raise TypeError(msg)
                if origin := get_origin(value_type):
                    if origin in (list, dict):
                        return  # no coercion needed
                    msg = (
                        f"{cls.__name__}: unsupported parameterized value type. "
                        f"Only list and dict supported, got {value_type!r}"
                    )
                    raise TypeError(msg)
                if isinstance(value_type, type):
                    cls._value_type = value_type
                else:
                    msg = f"{cls.__name__}: value type must be a concrete type, got {value_type!r}"
                    raise TypeError(msg)
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
    def load(cls: type[KVC], path: str) -> KVC:
        return _get_or_create_instance(cls, path)

    def reload(self) -> None:
        _reload_file_instance(self)

    def save(self, *args: Any, **kwargs: Any) -> bool:
        self.update(*args, **kwargs)
        return _save_cached_file_instance(self, dict(self.items()))
