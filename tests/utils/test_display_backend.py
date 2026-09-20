from __future__ import annotations

from typing import cast

import pytest
from pytest_mock import MockerFixture

from ulauncher.utils.display_backend import preferred_backend, xwayland_preferable_for_de
from ulauncher.utils.settings import DisplayBackend


@pytest.mark.parametrize(
    ("display_backend", "external_backend", "expected"),
    [
        # An explicit x11 setting overrides the environment.
        ("x11", None, "x11"),
        ("x11", "wayland", "x11"),
        # An exported GDK_BACKEND overrides auto and system.
        ("auto", "wayland", "wayland"),
        ("system", "x11", "x11"),
        # Without an export, system keeps the session default.
        ("system", None, None),
    ],
)
def test_preferred_backend(display_backend: DisplayBackend, external_backend: str | None, expected: str | None) -> None:
    assert preferred_backend(display_backend, external_backend) == expected


@pytest.mark.parametrize(
    ("stored_value", "de_verdict", "external_backend", "expected"),
    [
        # The UI falls back to showing Auto for values missing from the dropdown; so must the resolver
        ("prefer_x11", False, None, None),
        # The normalized value feeds the DE verdict, which picks XWayland here
        ("prefer_x11", True, None, "x11"),
        # An export still wins over a normalized value
        ("prefer_x11", False, "wayland", "wayland"),
    ],
)
def test_preferred_backend__unknown_value_is_auto(
    mocker: MockerFixture, stored_value: str, de_verdict: bool, external_backend: str | None, expected: str | None
) -> None:
    mocker.patch("ulauncher.utils.display_backend.xwayland_preferable_for_de", return_value=de_verdict)
    assert preferred_backend(cast("DisplayBackend", stored_value), external_backend) == expected


@pytest.mark.parametrize(
    ("prefer_xwayland", "expected"),
    [(True, "x11"), (False, None)],
)
def test_preferred_backend__auto_follows_de_verdict(
    mocker: MockerFixture, prefer_xwayland: bool, expected: str | None
) -> None:
    mocker.patch("ulauncher.utils.display_backend.xwayland_preferable_for_de", return_value=prefer_xwayland)
    assert preferred_backend("auto", None) == expected


@pytest.mark.parametrize(
    ("shell_version", "expected"),
    [
        (None, False),
        (49, False),
        (50, True),
    ],
)
def test_xwayland_preferable_for_de__gnome_version_boundary(
    mocker: MockerFixture, shell_version: int | None, expected: bool
) -> None:
    mocker.patch("ulauncher.utils.display_backend.DESKTOP_ID", "GNOME")
    mocker.patch("ulauncher.utils.display_backend.IS_X11", False)
    mocker.patch("ulauncher.utils.display_backend.gnome_shell_major_version", return_value=shell_version)
    assert xwayland_preferable_for_de() is expected
