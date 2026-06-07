from __future__ import annotations

from ulauncher.internals import effect_utils, effects


class TestShouldClose:
    """Tests for the is_closing_effect function."""

    def test_result_list_keeps_window_open(self) -> None:
        """Result list should should keep the window open."""
        assert not effect_utils.should_close([])

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


class TestConvertToEffectMessage:
    def test_iterable_results_are_collected(self) -> None:
        from ulauncher.internals.result import Result

        results = [Result(name="a"), Result(name="b")]
        assert effect_utils.convert_to_effect_message(iter(results)) == results

    def test_yielded_lists_replace_previous_results(self) -> None:
        """Mirrors the streamed semantics: a yielded list replaces, a Result appends."""
        from ulauncher.internals.result import Result

        def listener_output():  # noqa: ANN202
            yield [Result(name="answer: hello")]
            yield [Result(name="answer: hello world!")]
            yield Result(name="extra item")

        converted = effect_utils.convert_to_effect_message(listener_output())
        assert isinstance(converted, list)
        assert [result.name for result in converted] == ["answer: hello world!", "extra item"]
