from __future__ import annotations

from copy import deepcopy
from typing import TYPE_CHECKING, Any, Callable, Dict, TypeVar

from ulauncher.utils.lru_cache import lru_cache

if TYPE_CHECKING:
    from typing_extensions import dataclass_transform, deprecated
else:
    # Type-check-only decorator (PEP 681). typing_extensions must stay out of the runtime,
    # and typing.dataclass_transform needs py3.11, so at runtime this is a no-op.
    _T = TypeVar("_T")

    def dataclass_transform(**_kwargs: Any) -> Callable[[_T], _T]:
        return lambda cls: cls


@lru_cache(maxsize=None)
def _class_defaults(cls: type) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for base_cls in reversed(cls.__mro__):
        if base_cls in BaseDataClass.__mro__:
            continue
        result.update(
            {k: v for k, v in vars(base_cls).items() if not k.startswith("__") and not callable(getattr(base_cls, k))}
        )
    return result


def _apply_class_defaults(instance: BaseDataClass) -> None:
    # deep copy to handle https://stackoverflow.com/q/1132941/633921
    instance.update(deepcopy(_class_defaults(type(instance))))


@dataclass_transform(kw_only_default=True, eq_default=False)
class BaseDataClass(Dict[str, Any]):
    """
    BaseDataClass

    Custom lightweight alternative to dataclasses, that work in older Python versions from before dataclasses.
    * Intentionally does not support positional arguments (because of https://stackoverflow.com/q/51575931/633921).
    * Does not need decorators to declare class props.
    * Ensures type consistency for properties declared in class
    * Unlike dataclasses, new props (set at runtime, but undeclared in the class) become part of the data.
    * Implemented using the AttrDict pattern, but it avoids self.__dict__ = self

    * Annotated props become constructor keywords for type checkers (PEP 681), so annotate every field.
    * Removing a declared prop is a type-check-only error. Nothing enforces it at runtime.

    # Example use:
    class Person(BaseDataClass):
        # All props you declare need a type annotation.
        first_name: str  # Required (no default)
        last_name: str | None = None  # Optional with a default
        age: int | None = None
        metadata: dict[str, str] = {}  # Cloned per instance, so you can ignore linter warnings

        def full_name(self):
            return f"{self.first_name} {self.last_name}" if self.last_name else self.first_name

    print(Person(first_name="John", last_name="Wayne").full_name()) # John Wayne
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__()
        _apply_class_defaults(self)
        self.update(*args, **kwargs)

    def clear(self) -> None:
        """Reset to class defaults, removing any runtime-added keys.

        Props declared without a default stay absent, which is why type checkers reject this call.
        Subclasses whose props all have defaults re-declare it to opt back in.
        """
        super().clear()
        _apply_class_defaults(self)

    def __hash__(self) -> int:  # type: ignore [override]
        """
        Returns the memory address of the instance as a hash, so even if it's mutable this remains consistent.
        """
        return id(self)

    def __dir__(self) -> list[str]:  # For IDE autocompletion
        return dir(type(self)) + list(self.keys())

    def __delattr__(self, key: str) -> None:
        # Subscript form, so a subclass __delitem__ still runs.
        del self[key]  # type: ignore[deprecated]

    def __getattribute__(self, key: str) -> Any:
        try:
            return self[key]
        except KeyError:
            return super().__getattribute__(key)

    def __setattr__(self, key: str, value: Any) -> None:
        self[key] = value

    @classmethod
    def accepts_key(cls, key: str) -> bool:
        """Whether key can be stored without shadowing a class member.

        Setting a rejected key raises, so filter untrusted data (file contents) through this.
        """
        if not hasattr(cls, key):
            return True
        return not key.startswith("__") and not callable(getattr(cls, key))

    def __setitem__(self, key: str, value: Any) -> None:
        if not self.accepts_key(key):
            msg = f'Invalid property "{key}". Must not override a class member.'
            raise KeyError(msg)

        super().__setitem__(key, value)

    # Make sure everything flows through __setitem__
    def update(self, *args: Any, **kwargs: Any) -> None:
        for k, v in dict(*args, **kwargs).items():
            self[k] = v

    if TYPE_CHECKING:
        # Signatures only, so the runtime keeps the inherited behavior. Must come after the real
        # definitions to be the ones type checkers see.

        @deprecated("Removes a declared prop. Build a new instance instead.")
        def __delitem__(self, key: str) -> None: ...

        @deprecated("Removes a declared prop. Build a new instance instead.")
        def __delattr__(self, key: str) -> None: ...

        @deprecated("Removes a declared prop. Use `get` if you only need to read it.")
        def pop(self, *args: Any, **kwargs: Any) -> Any: ...

        @deprecated("Removes a declared prop. Build a new instance instead.")
        def popitem(self) -> tuple[str, Any]: ...

        @deprecated("Drops props declared without a default. Build a new instance instead.")
        def clear(self) -> None: ...
