from types import SimpleNamespace
from typing import Any, cast
from unittest.mock import MagicMock

from pytest_mock import MockerFixture

from ulauncher.ui.ulauncher_window import UlauncherWindow


def _make_window(max_content_height: int, current_min: int) -> SimpleNamespace:
    scroller = MagicMock()
    scroller.get_property.return_value = max_content_height
    scroller.get_min_content_height.return_value = current_min
    # GTK widgets cannot be built without a display; the method only touches the scroller
    window = cast("Any", SimpleNamespace(results_scroller=scroller, _has_wrapped_results=True))
    box = MagicMock()
    return SimpleNamespace(window=window, scroller=scroller, box=box)


def test_fit_results_height__requests_the_height_for_width(mocker: MockerFixture) -> None:
    run_when_idle = mocker.patch("ulauncher.ui.ulauncher_window.scheduling.run_when_idle")
    setup = _make_window(max_content_height=600, current_min=46)
    setup.box.get_preferred_height_for_width.return_value = (180, 180)

    UlauncherWindow._fit_results_height(setup.window, setup.box, cast("Any", SimpleNamespace(width=500)))

    setup.box.get_preferred_height_for_width.assert_called_once_with(500)
    setup.scroller.set_min_content_height.assert_called_once_with(180)
    run_when_idle.assert_called_once()


def test_fit_results_height__clamps_to_max_content_height(mocker: MockerFixture) -> None:
    mocker.patch("ulauncher.ui.ulauncher_window.scheduling.run_when_idle")
    setup = _make_window(max_content_height=600, current_min=46)
    setup.box.get_preferred_height_for_width.return_value = (2000, 2000)

    UlauncherWindow._fit_results_height(setup.window, setup.box, cast("Any", SimpleNamespace(width=500)))

    setup.scroller.set_min_content_height.assert_called_once_with(600)


def test_fit_results_height__noop_when_height_is_unchanged(mocker: MockerFixture) -> None:
    run_when_idle = mocker.patch("ulauncher.ui.ulauncher_window.scheduling.run_when_idle")
    setup = _make_window(max_content_height=600, current_min=180)
    setup.box.get_preferred_height_for_width.return_value = (180, 180)

    UlauncherWindow._fit_results_height(setup.window, setup.box, cast("Any", SimpleNamespace(width=500)))

    setup.scroller.set_min_content_height.assert_not_called()
    run_when_idle.assert_not_called()  # no resize requeued: would loop on every allocation


def test_fit_results_height__inactive_without_wrapped_results(mocker: MockerFixture) -> None:
    run_when_idle = mocker.patch("ulauncher.ui.ulauncher_window.scheduling.run_when_idle")
    setup = _make_window(max_content_height=600, current_min=180)
    setup.window._has_wrapped_results = False

    UlauncherWindow._fit_results_height(setup.window, setup.box, cast("Any", SimpleNamespace(width=500)))

    # stock sizing is restored so a previous wrapped query cannot ratchet the height
    setup.scroller.set_min_content_height.assert_called_once_with(-1)
    setup.box.get_preferred_height_for_width.assert_not_called()
    run_when_idle.assert_not_called()


def test_fit_results_height__skips_early_allocation_passes(mocker: MockerFixture) -> None:
    run_when_idle = mocker.patch("ulauncher.ui.ulauncher_window.scheduling.run_when_idle")
    setup = _make_window(max_content_height=600, current_min=46)

    UlauncherWindow._fit_results_height(setup.window, setup.box, cast("Any", SimpleNamespace(width=0)))

    setup.scroller.set_min_content_height.assert_not_called()
    run_when_idle.assert_not_called()


def test_fit_results_height__tolerates_one_pixel_oscillation(mocker: MockerFixture) -> None:
    run_when_idle = mocker.patch("ulauncher.ui.ulauncher_window.scheduling.run_when_idle")
    setup = _make_window(max_content_height=600, current_min=180)
    setup.box.get_preferred_height_for_width.return_value = (181, 181)

    UlauncherWindow._fit_results_height(setup.window, setup.box, cast("Any", SimpleNamespace(width=500)))

    setup.scroller.set_min_content_height.assert_not_called()
    run_when_idle.assert_not_called()
