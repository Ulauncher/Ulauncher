from __future__ import annotations

from typing import Any, TypeVar

from ulauncher.data._file_cache import _get_or_create_instance, _reload_file_instance, _save_cached_file_instance
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

    @classmethod
    def load(cls: type[T], path: str) -> T:
        return _get_or_create_instance(cls, path)

    def reload(self) -> None:
        _reload_file_instance(self)

    def save(self, *args: Any, **kwargs: Any) -> bool:
        self.update(*args, **kwargs)
        return _save_cached_file_instance(self, self, sort_keys=True)
