from unittest.mock import Mock

import pytest

from ulauncher.utils.eventbus import EventBus


class TestEmit:
    def test_calls_all_listeners(self) -> None:
        bus = EventBus("test-emit")
        listener = Mock()

        @bus.on
        def event_a() -> None:
            listener()

        bus.emit("test-emit:event_a")
        listener.assert_called_once_with()

    def test_raising_listener_is_logged_and_does_not_break_the_others(self, caplog: pytest.LogCaptureFixture) -> None:
        bus = EventBus("test-isolation")
        survivor = Mock()

        @bus.on
        def event_b() -> None:
            msg = "boom"
            raise RuntimeError(msg)

        @bus.on
        def event_b() -> None:  # type: ignore[no-redef]  # noqa: F811
            survivor()

        bus.emit("test-isolation:event_b")
        survivor.assert_called_once_with()
        assert "Unhandled error in listener for event test-isolation:event_b" in caplog.text
