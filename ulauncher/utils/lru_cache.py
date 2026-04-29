from __future__ import annotations

from functools import lru_cache as _lru_cache
from typing import TYPE_CHECKING, cast

if TYPE_CHECKING:
    from typing import Callable, TypeVar

    from typing_extensions import ParamSpec

    P = ParamSpec("P")
    R = TypeVar("R")


# functools.lru_cache wraps functions in _lru_cache_wrapper whose __call__ is typed as
# (*args: Hashable, **kwargs: Hashable) -> T, erasing all parameter types.
# This wrapper uses ParamSpec to preserve the original signature so type
# checkers can enforce argument types at every call site.
def lru_cache(maxsize: int | None = 128) -> Callable[[Callable[P, R]], Callable[P, R]]:
    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        return cast("Callable[P, R]", _lru_cache(maxsize=maxsize)(func))

    return decorator  # type: ignore[return-value]
