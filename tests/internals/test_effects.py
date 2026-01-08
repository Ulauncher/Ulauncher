from __future__ import annotations

from ulauncher.internals import effects


class TestShouldClose:
    """Tests for the is_closing_effect function."""

    def test_result_list_keeps_window_open(self) -> None:
        """Result list should should keep the window open."""
        assert not effects.should_close([])

    def test_set_query_keeps_window_open(self) -> None:
        """SET_QUERY effect should keep the window open."""
        effect = effects.set_query("test query")
        assert not effects.should_close(effect)

    def test_do_nothing_keeps_window_open(self) -> None:
        """DO_NOTHING effect should keep the window open."""
        effect = effects.do_nothing()
        assert not effects.should_close(effect)

    def test_close_window_closes(self) -> None:
        """CLOSE_WINDOW effect should close the window."""
        effect = effects.close_window()
        assert effects.should_close(effect)

    def test_open_closes_window(self) -> None:
        """OPEN effect should close the window."""
        effect = effects.open("/path/to/file")
        assert effects.should_close(effect)

    def test_copy_closes_window(self) -> None:
        """COPY effect should close the window."""
        effect = effects.copy("text to copy")
        assert effects.should_close(effect)

    def test_run_script_closes_window(self) -> None:
        """LEGACY_RUN_SCRIPT effect should close the window."""
        effect = effects.run_script("#!/bin/bash\necho test")
        assert effects.should_close(effect)

    def test_effect_list_with_do_nothing_keeps_open(self) -> None:
        """Effect list with DO_NOTHING should keep the window open."""
        effect = effects.effect_list(
            [
                effects.close_window(),
                effects.do_nothing(),
            ]
        )
        assert not effects.should_close(effect)

    def test_effect_list_with_set_query_keeps_open(self) -> None:
        """Effect list with SET_QUERY should keep the window open."""
        effect = effects.effect_list(
            [
                effects.open("/path"),
                effects.set_query("new query"),
            ]
        )
        assert not effects.should_close(effect)

    def test_effect_list_empty_closes(self) -> None:
        """Empty effect list should close the window"""
        effect = effects.effect_list([])
        assert effects.should_close(effect)

    def test_nested_effect_list_with_non_closing(self) -> None:
        """Nested effect list with any non-closing effect should keep open."""
        inner = effects.effect_list(
            [
                effects.close_window(),
                effects.do_nothing(),
            ]
        )
        outer = effects.effect_list(
            [
                effects.open("/path"),
                inner,
            ]
        )
        assert not effects.should_close(outer)
