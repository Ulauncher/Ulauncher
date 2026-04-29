from __future__ import annotations

from functools import lru_cache as _lru_cache
from typing import TYPE_CHECKING, cast

if TYPE_CHECKING:
    from typing import Callable, TypeVar, overload

    from typing_extensions import ParamSpec

    P = ParamSpec("P")
    R = TypeVar("R")


# functools.lru_cache wraps functions in _lru_cache_wrapper whose __call__ is typed as
# (*args: Hashable, **kwargs: Hashable) -> T, erasing all parameter types.
# This wrapper uses ParamSpec to preserve the original signature so type
# checkers can enforce argument types at every call site.
if TYPE_CHECKING:

    @overload
    def lru_cache(maxsize: Callable[P, R]) -> Callable[P, R]: ...

    @overload
    def lru_cache(maxsize: int | None = 128, typed: bool = False) -> Callable[[Callable[P, R]], Callable[P, R]]: ...


def lru_cache(
    maxsize: Callable[P, R] | int | None = 128, typed: bool = False
) -> Callable[[Callable[P, R]], Callable[P, R]] | Callable[P, R]:
    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        return cast("Callable[P, R]", _lru_cache(maxsize=maxsize, typed=typed)(func))

    if callable(maxsize):
        return cast("Callable[P, R]", _lru_cache(typed=typed)(maxsize))

    return decorator  # type: ignore[return-value]
