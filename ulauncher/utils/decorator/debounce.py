from __future__ import annotations

import contextlib
from functools import wraps
from typing import TYPE_CHECKING, Any, Callable, cast

from ulauncher.utils.timer import timer

if TYPE_CHECKING:
    from typing_extensions import ParamSpec

    P = ParamSpec("P")


def debounce(wait: float) -> Callable[[Callable[P, Any]], Callable[P, None]]:
    """Decorator that will postpone a function
    execution until after wait seconds
    have elapsed since the last time it was invoked."""

    def decorator(fn: Callable[P, Any]) -> Callable[P, None]:
        @wraps(fn)
        def debounced(*args: Any, **kwargs: Any) -> None:
            def call_it() -> None:
                fn(*args, **kwargs)

            with contextlib.suppress(AttributeError):
                debounced.t.cancel()  # type: ignore[attr-defined]

            debounced.t = timer(wait, call_it)  # type: ignore[attr-defined]

        return cast("Callable[P, None]", debounced)

    return decorator  # type: ignore[return-value]
