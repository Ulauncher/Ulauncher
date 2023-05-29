import contextlib

from ulauncher.utils.timer import timer


def debounce(wait):
    """Decorator that will postpone a functions
    execution until after wait seconds
    have elapsed since the last time it was invoked."""

    def decorator(fn):
        def debounced(*args, **kwargs):
            def call_it():
                fn(*args, **kwargs)

            with contextlib.suppress(AttributeError):
                debounced.t.cancel()

            debounced.t = timer(wait, call_it)

        return debounced

    return decorator
