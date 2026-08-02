from __future__ import annotations

import os
import warnings
from typing import Any, TextIO

from ulauncher.api._logging import get_extension_logger


class ApiDeprecationWarning(DeprecationWarning):
    """Emitted when an extension uses the pre-v3 (v2) Ulauncher extension API."""


# Set by the app only for v3 extensions. v2 extensions already get a compatibility-mode warning,
# and standalone runs (unset) stay quiet.
_enabled = os.getenv("ULAUNCHER_API_DEPRECATION_WARNINGS") == "1"


def _install_logging_showwarning() -> None:
    default_showwarning = warnings.showwarning

    def showwarning(
        message: Warning | str,
        category: type[Warning],
        filename: str,
        lineno: int,
        file: TextIO | None = None,
        line: str | None = None,
    ) -> None:
        if issubclass(category, ApiDeprecationWarning):
            get_extension_logger().warning("%s (%s:%s)", message, filename, lineno)
            return
        default_showwarning(message, category, filename, lineno, file, line)

    warnings.showwarning = showwarning


if _enabled:
    # "once" dedups by message, and also enables DeprecationWarning outside __main__
    warnings.filterwarnings("once", category=ApiDeprecationWarning)
    _install_logging_showwarning()


def warn_legacy_import(module: str) -> None:
    if not _enabled:
        return
    warnings.warn(
        f"Importing from `{module}` is deprecated. It is part of the Ulauncher extension API v2 and "
        "will be removed in a future release. Use the v3 API in `ulauncher.api` instead.",
        ApiDeprecationWarning,
        stacklevel=2,
    )


def warn_legacy_api(name: str, hint: str, stacklevel: int = 3) -> None:
    if not _enabled:
        return
    warnings.warn(
        f"`{name}` is deprecated (Ulauncher extension API v2). {hint}", ApiDeprecationWarning, stacklevel=stacklevel
    )


# The v2 result classes took these four positionally, in this order.
_LEGACY_POSITIONAL_FIELDS = ("name", "description", "keyword", "icon")


def merge_legacy_positional_args(name: str, args: tuple[Any, ...], kwargs: dict[str, Any]) -> dict[str, Any]:
    """Map positionally passed v2 result arguments onto their field names."""
    if not args:
        return kwargs
    if len(args) > len(_LEGACY_POSITIONAL_FIELDS):
        # A 5th arg used to be `include_in_results`, which no longer exists. Binding it to a later
        # field would silently change meaning, so reject it instead.
        msg = f"{name} takes at most {len(_LEGACY_POSITIONAL_FIELDS)} positional arguments ({len(args)} given)"
        raise TypeError(msg)
    warn_legacy_api(
        f"{name}({', '.join(_LEGACY_POSITIONAL_FIELDS)})",
        "Pass these fields by name instead, e.g. `Result(name=...)`.",
        stacklevel=4,  # this helper sits between the caller's __init__ and warn_legacy_api
    )
    positional = dict(zip(_LEGACY_POSITIONAL_FIELDS, args))
    for field in positional.keys() & kwargs.keys():
        msg = f"{name} got multiple values for argument '{field}'"
        raise TypeError(msg)
    return {**positional, **kwargs}
