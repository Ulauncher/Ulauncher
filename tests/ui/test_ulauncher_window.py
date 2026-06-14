from __future__ import annotations

from types import SimpleNamespace
from typing import Any, cast
from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture

from ulauncher.ui.ulauncher_window import UlauncherWindow


class TestUlauncherWindow:
    @pytest.mark.parametrize(
        ("has_wrapped", "width", "current_min", "needed", "measured_width", "expected_min", "expects_resize"),
        [
            pytest.param(True, 500, 46, 180, 500, 180, True, id="requests_the_height_for_width"),
            pytest.param(True, 500, 46, 2000, 500, 600, True, id="clamps_to_max_content_height"),
            pytest.param(True, 500, 180, 180, 500, None, False, id="noop_when_height_is_unchanged"),
            pytest.param(True, 500, 180, 181, 500, None, False, id="tolerates_one_pixel_oscillation"),
            pytest.param(True, 0, 46, 180, None, None, False, id="skips_early_allocation_passes"),
            pytest.param(False, 500, 180, 180, None, None, False, id="noop_without_wrapped_results"),
        ],
    )
    def test_fit_results_height(
        self,
        mocker: MockerFixture,
        has_wrapped: bool,
        width: int,
        current_min: int,
        needed: int,
        measured_width: int | None,
        expected_min: int | None,
        expects_resize: bool,
    ) -> None:
        run_when_idle = mocker.patch("ulauncher.ui.ulauncher_window.scheduling.run_when_idle")
        scroller = MagicMock()
        scroller.get_property.return_value = 600  # max-content-height
        scroller.get_min_content_height.return_value = current_min
        box = MagicMock()
        box.get_preferred_height_for_width.return_value = (needed, needed)
        # GTK widgets cannot be built without a display; the method only touches the scroller
        window = cast("Any", SimpleNamespace(results_scroller=scroller, _has_wrapped_results=has_wrapped))

        UlauncherWindow._fit_results_height(window, box, cast("Any", SimpleNamespace(width=width)))

        if measured_width is None:
            box.get_preferred_height_for_width.assert_not_called()
        else:
            box.get_preferred_height_for_width.assert_called_once_with(measured_width)

        if expected_min is None:
            scroller.set_min_content_height.assert_not_called()
        else:
            scroller.set_min_content_height.assert_called_once_with(expected_min)

        assert run_when_idle.called is expects_resize
