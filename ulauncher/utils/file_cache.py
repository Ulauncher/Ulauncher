from __future__ import annotations

import hashlib
import os
import pickle
from datetime import datetime, timedelta
from functools import lru_cache, wraps
from typing import Any, Callable, TypeVar, cast

from ulauncher.paths import CACHE_DIR

Ret = TypeVar("Ret")


def file_cache(
    *, expiry: timedelta | None = None, cache_none: bool = True
) -> Callable[[Callable[..., Ret]], Callable[..., Ret]]:
    def decorator(func: Callable[..., Ret]) -> Callable[..., Ret]:
        module_name = func.__module__.replace(".", "_")
        cache_file_name = f"file_cache__{module_name}__{func.__name__}"
        # make sure file name length is longer than 255 chars. Truncate if necessary
        cache_file_name = cache_file_name[:255]

        @wraps(func)
        def wrapped(*args: Any, **kwargs: Any) -> Ret:
            cache: dict[str, CacheEntry] = load_cache(cache_file_name) or {}
            key = hash_args(args, kwargs)

            if key in cache:
                return cast("Ret", cache[key].value)

            result = func(*args, **kwargs)

            if not cache_none and result is None:
                return cast("Ret", result)

            expiry_time = datetime.now() + expiry if expiry else None
            cache[key] = CacheEntry(value=result, expiry=expiry_time)
            save_cache(cache_file_name, cache)

            return result

        return wrapped

    return decorator


class CacheEntry:
    def __init__(self, value: Any, expiry: datetime | None = None) -> None:
        self.value = value
        self.expiry = expiry


def hash_args(args: tuple[Any, ...], kwargs: dict[Any, Any]) -> str:
    try:
        return hashlib.md5(pickle.dumps((args, frozenset(kwargs.items())))).hexdigest()
    except (TypeError, pickle.PicklingError) as e:
        msg = "Arguments must be hashable"
        raise TypeError(msg) from e


@lru_cache(maxsize=1000)
def load_cache(cache_file_name: str) -> dict[str, CacheEntry] | None:
    full_path = os.path.join(CACHE_DIR, cache_file_name)
    if not os.path.exists(full_path):
        return None
    with open(full_path, "rb") as f:
        return cast("dict[str, CacheEntry]", pickle.load(f))


def save_cache(cache_file_name: str, data: dict[str, CacheEntry]) -> None:
    full_path = os.path.join(CACHE_DIR, cache_file_name)
    with open(full_path, "wb") as f:
        pickle.dump(data, f)
