import gi
gi.require_version('GdkX11', '3.0')
# pylint: disable=wrong-import-position

from gi.repository import GdkX11  # type: ignore

import pytest

is_display_enabled = bool(GdkX11.X11Display.get_default())


def pytest_configure(config):
    config.addinivalue_line("markers", "with_display: skip test if no display is available")


def pytest_runtest_setup(item):
    if isinstance(item, pytest.Function):
        if any(item.iter_markers('with_display')) and not is_display_enabled:
            pytest.skip("Cannot run without a display enabled.")
