from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ulauncher.data._file_cache import _load_cached_file_instance, _save_cached_file_instance
from ulauncher.data.base_data_class import BaseDataClass

if TYPE_CHECKING:
    from typing_extensions import Self


class JsonConf(BaseDataClass):
    """
    JsonConf

    This is an helper class to handle json config files
    It has two convenient methods for loading and saving the data, which also depuplicate class instances,
    So that if you create two instances for the same file it will actually reuse the first instance
    (to avoid overwriting state changes)

    File paths are stored in an external reference object, which is not part of the data.
    """

    if TYPE_CHECKING:
        # Declaring __init__ opts this class out of the PEP 681 field synthesis, which would otherwise
        # reject the arbitrary keys it holds. It is only a signature, so it stays out of the runtime and
        # BaseDataClass.__init__ keeps handling construction. Subclasses that declare fields don't
        # override __init__, so they still get the synthesis.
        def __init__(self, *args: Any, **kwargs: Any) -> None: ...  # pylint: disable=super-init-not-called

        # Opts back in to clear. Safe here because file data is partial, so every prop needs a default.
        def clear(self) -> None: ...

    @classmethod
    def load(cls, path: str, *, force: bool = False) -> Self:
        return _load_cached_file_instance(cls, path, force=force)

    def save(self, *args: Any, **kwargs: Any) -> bool:
        self.update(*args, **kwargs)
        return _save_cached_file_instance(self, self, sort_keys=True)
