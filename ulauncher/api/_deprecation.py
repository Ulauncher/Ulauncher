from __future__ import annotations

import os
import warnings
from typing import TextIO

from ulauncher.api._logging import get_extension_logger


class ApiDeprecationWarning(DeprecationWarning):
    """Emitted when an extension uses the pre-v3 (v2) Ulauncher extension API."""


# Set by the app only for v3 extensions. v2 extensions already get a compatibility-mode warning,
# and standalone runs (unset) stay quiet.
_enabled = os.getenv("ULAUNCHER_API_DEPRECATION_WARNINGS") == "1"
_logger = get_extension_logger()


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
            _logger.warning("%s (%s:%s)", message, filename, lineno)
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


def warn_legacy_api(name: str, hint: str) -> None:
    if not _enabled:
        return
    warnings.warn(f"`{name}` is deprecated (Ulauncher extension API v2). {hint}", ApiDeprecationWarning, stacklevel=3)
