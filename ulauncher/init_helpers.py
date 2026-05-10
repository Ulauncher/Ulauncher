from __future__ import annotations

import os

from ulauncher import paths


def ensure_runtime_dirs() -> None:
    """Validate installation assets and create any missing directories required by the runtime."""
    if not os.path.exists(paths.ASSETS):
        raise OSError(paths.ASSETS)

    for path in (
        paths.CONFIG,
        paths.STATE,
        paths.USER_EXTENSIONS,
        paths.EXTENSIONS_CONFIG,
        paths.USER_THEMES,
    ):
        os.makedirs(path, exist_ok=True)


def configure_logging(*, verbose: bool, use_app_logging: bool) -> None:
    import logging

    handlers: list[logging.Handler] = []
    log_level = logging.DEBUG if verbose else logging.WARNING if use_app_logging else logging.INFO
    log_format = "%(message)s"
    stream_handler = logging.StreamHandler()

    if use_app_logging:
        from ulauncher.utils.logging_color_formatter import ColoredFormatter

        stream_handler.setFormatter(ColoredFormatter())
        log_format = "%(asctime)s | %(levelname)s | %(message)s | %(module)s.%(funcName)s():%(lineno)s"
        handlers.append(logging.FileHandler(paths.LOG_FILE, mode="w+"))

    stream_handler.setLevel(log_level)
    handlers.append(stream_handler)

    logging.getLogger("asyncio").setLevel(logging.WARNING)
    logging.root.handlers = []
    logging.basicConfig(
        level=logging.DEBUG,
        format=log_format,
        handlers=handlers,
    )


def init_x11_threads() -> None:
    """Initialize Xlib thread support before importing GTK on X11-compatible sessions."""
    from ctypes import cdll

    from ulauncher.utils.environment import IS_X11_COMPATIBLE

    if not IS_X11_COMPATIBLE:
        return

    # Using libX11.so.6 may seem a bit hard-coded, but a quick search on the Internet indicates
    # discussion of this ABI version back to before 2009, 12 years prior to when this code was added.
    # Also, with most of the development focus on Wayland, the chance of a ABI version bump in X11 is
    # exceptionally small. Therefore, no additional fancy discovery methods are necessary.
    try:
        x11 = cdll.LoadLibrary("libX11.so.6")
    except OSError as e:
        err_msg = "Failed to load libX11.so.6. Ensure X11 libraries are installed on your system."
        raise OSError(err_msg) from e

    # In order to use any X11 calls from multiple threads, the X11 library must be initialized to use
    # mutex protection. XInitThreads() sets this up and must be called before any other X11
    # initialization is performed.
    x11.XInitThreads()
