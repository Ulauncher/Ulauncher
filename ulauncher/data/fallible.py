"""
Lightweight errors-as-values type for synchronous functions where failure is an expected
outcome the caller must branch on. See docs/architecture/error-handling.md.

There is deliberately no unwrap() or value-with-default accessor: the only way to reach
the value is to narrow with isinstance, so the type checker proves every caller handles
the failure path.

    outcome = parse_thing(raw)
    if isinstance(outcome, Err):
        return notify(outcome.error)
    use(outcome.value)
"""

from __future__ import annotations

from typing import Generic, TypeVar, Union

T = TypeVar("T")
E = TypeVar("E")


class Ok(Generic[T]):
    __slots__ = ("value",)

    def __init__(self, value: T) -> None:
        self.value = value

    def __repr__(self) -> str:
        return f"Ok({self.value!r})"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Ok) and other.value == self.value

    def __hash__(self) -> int:
        return hash((Ok, self.value))


class Err(Generic[E]):
    __slots__ = ("error",)

    def __init__(self, error: E) -> None:
        self.error = error

    def __repr__(self) -> str:
        return f"Err({self.error!r})"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Err) and other.error == self.error

    def __hash__(self) -> int:
        return hash((Err, self.error))


Fallible = Union[Ok[T], Err[E]]
