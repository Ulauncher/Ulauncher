from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture

from ulauncher.internals import effect_utils, effects


def run_many(*children: effects.EffectMessage) -> effects.LegacyRunMany:
    """Build a legacy ActionList effect without going through the deprecated api shim."""
    return {"type": effects.EffectType.LEGACY_RUN_MANY, "effects": list(children)}


class TestShouldClose:
    """Tests for the is_closing_effect function."""

    def test_result_list_keeps_window_open(self) -> None:
        """Result list should should keep the window open."""
        assert not effect_utils.should_close(effects.render_results([]))

    def test_set_query_keeps_window_open(self) -> None:
        """SET_QUERY effect should keep the window open."""
        effect = effects.set_query("test query")
        assert not effect_utils.should_close(effect)

    def test_do_nothing_keeps_window_open(self) -> None:
        """DO_NOTHING effect should keep the window open."""
        effect = effects.do_nothing()
        assert not effect_utils.should_close(effect)

    def test_close_window_closes(self) -> None:
        """CLOSE_WINDOW effect should close the window."""
        effect = effects.close_window()
        assert effect_utils.should_close(effect)

    def test_open_closes_window(self) -> None:
        """OPEN effect should close the window."""
        effect = effects.open("/path/to/file")
        assert effect_utils.should_close(effect)


class TestHandle:
    """Tests for the handle function."""

    @pytest.fixture
    def emit(self, mocker: MockerFixture) -> MagicMock:
        """Spy receiving every eventbus emit handle makes."""
        return mocker.patch.object(effect_utils, "_events").emit

    @pytest.fixture
    def open_detached(self, mocker: MockerFixture) -> MagicMock:
        """Stub the lazily imported launcher, so OPEN effects don't spawn anything."""
        return mocker.patch("ulauncher.utils.launch_detached.open_detached")

    def test_set_query_emits_without_closing(self, emit: MagicMock) -> None:
        effect_utils.handle(effects.set_query("hello"))
        emit.assert_called_once_with("app:set_query", "hello")

    def test_open_launches_and_closes(self, emit: MagicMock, open_detached: MagicMock) -> None:
        effect_utils.handle(effects.open("/path/to/file"))
        open_detached.assert_called_once_with("/path/to/file")
        emit.assert_called_once_with("app:close_launcher")

    def test_prevent_close_suppresses_the_close(self, emit: MagicMock, open_detached: MagicMock) -> None:
        effect_utils.handle(effects.open("/path/to/file"), prevent_close=True)
        open_detached.assert_called_once_with("/path/to/file")
        emit.assert_not_called()

    def test_run_many_dispatches_children_and_closes_once(self, emit: MagicMock, open_detached: MagicMock) -> None:
        effect_utils.handle(run_many(effects.open("/a"), effects.close_window()))
        open_detached.assert_called_once_with("/a")
        emit.assert_called_once_with("app:close_launcher")

    def test_run_many_keeps_window_open_unless_every_child_closes(
        self, emit: MagicMock, open_detached: MagicMock
    ) -> None:
        effect_utils.handle(run_many(effects.open("/a"), effects.do_nothing()))
        open_detached.assert_called_once_with("/a")
        emit.assert_not_called()

    def test_run_many_skips_nested_renders(self, emit: MagicMock, open_detached: MagicMock) -> None:
        """Rendering belongs to the callers holding the query context, so handle drops it silently."""
        effect_utils.handle(run_many(effects.render_results([]), effects.open("/a")))
        open_detached.assert_called_once_with("/a")
        emit.assert_not_called()
