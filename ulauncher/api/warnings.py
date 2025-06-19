import warnings
from typing import Callable, TypeVar

from typing_extensions import ParamSpec

_P = ParamSpec("_P")
_OUT = TypeVar("_OUT")


def deprecation_warning(message: str) -> Callable[[Callable[_P, _OUT]], Callable[_P, _OUT]]:
    """
    Decorator to mark functions as deprecated with a custom message.
    """

    def decorator(func: Callable[_P, _OUT]) -> Callable[_P, _OUT]:
        def wrapper(*args: _P.args, **kwargs: _P.kwargs) -> _OUT:
            warnings.warn(
                f"{func.__name__} is deprecated and will be removed in v7: {message}", DeprecationWarning, stacklevel=2
            )
            return func(*args, **kwargs)

        return wrapper

    return decorator
