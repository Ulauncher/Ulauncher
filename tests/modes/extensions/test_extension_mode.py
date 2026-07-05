from __future__ import annotations

from types import SimpleNamespace
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, call

from pytest_mock import MockerFixture

from ulauncher.internals import effects
from ulauncher.internals.query import Query
from ulauncher.internals.result import Result
from ulauncher.modes.extensions.extension_record import ExtensionRecord

if TYPE_CHECKING:
    from ulauncher.modes.extensions.extension_mode import ExtensionMode


def _make_mode() -> ExtensionMode:
    from ulauncher.modes.extensions import extension_mode

    mode = object.__new__(extension_mode.ExtensionMode)
    mode._trigger_cache = {}
    return mode


def _mock_service(mocker: MockerFixture) -> MagicMock:
    from ulauncher.modes.extensions.extension_service import ext_service

    mocked = MagicMock()
    mocker.patch.object(ext_service, "get", mocked.get)
    mocker.patch.object(ext_service, "iterate", mocked.iterate)
    mocker.patch.object(ext_service, "is_running", mocked.is_running)
    return mocked


def test_handle_query__transitioning_extension_waits(mocker: MockerFixture) -> None:
    from ulauncher.modes.extensions import extension_mode

    mode = _make_mode()
    mode._trigger_cache = {"kw": ("trigger1", "test.ext")}
    ext = SimpleNamespace(id="test.ext")
    mocked_service = _mock_service(mocker)
    mocked_service.get.return_value = ext
    mocked_service.is_running.return_value = False
    timer = mocker.patch.object(extension_mode.scheduling, "timer", return_value=MagicMock())
    callback = MagicMock()

    mode.handle_query(Query("kw", "arg"), callback)

    callback.assert_not_called()
    timer.assert_called_once()
    assert mode._active_ext is ext


def test_handle_query__loading_timeout_shows_empty(mocker: MockerFixture) -> None:
    from ulauncher.modes.extensions import extension_mode

    mode = _make_mode()
    mode._trigger_cache = {"kw": ("trigger1", "test.ext")}
    ext = SimpleNamespace(id="test.ext")
    mocked_service = _mock_service(mocker)
    mocked_service.get.return_value = ext
    mocked_service.is_running.return_value = False
    timer = mocker.patch.object(extension_mode.scheduling, "timer", return_value=MagicMock())
    callback = MagicMock()

    mode.handle_query(Query("kw", "arg"), callback)
    timer.call_args.args[1]()  # fire the captured loading-timeout callback

    callback.assert_called_once_with(effects.render_results([]))
    assert mode._loading_timer is None


def test_handle_query__unknown_keyword_shows_message(mocker: MockerFixture) -> None:
    mode = _make_mode()
    mocked_service = _mock_service(mocker)
    mocked_service.iterate.return_value = iter([])
    mocked_service.get.return_value = None
    callback = MagicMock()

    mode.handle_query(Query("kw", "arg"), callback)

    callback.assert_called_once()
    (effect,) = callback.call_args.args
    assert [r.name for r in effect["results"]] == ["Extension not available"]


def test_errored__while_loading_shows_failure(mocker: MockerFixture) -> None:
    mode = _make_mode()
    mode._active_ext = _make_active_ext("test.ext")
    failure = Result(name="failed")
    mocker.patch.object(mode, "_loading_failed_result", return_value=failure)
    timer = MagicMock()
    mode._loading_timer = timer
    callback = MagicMock()
    mode._pending_callback = callback

    mode.errored("test.ext")

    callback.assert_called_once_with(effects.render_results([failure]))
    timer.cancel.assert_called_once()
    assert mode._loading_timer is None


def test_errored__while_not_loading_drops_pending_callback() -> None:
    mode = _make_mode()
    mode._active_ext = _make_active_ext("test.ext")
    callback = MagicMock()
    mode._pending_callback = callback

    mode.errored("test.ext")

    callback.assert_not_called()
    assert mode._pending_callback is None


def test_errored__ignores_other_extensions() -> None:
    mode = _make_mode()
    mode._active_ext = _make_active_ext("test.ext")
    timer = MagicMock()
    mode._loading_timer = timer
    callback = MagicMock()
    mode._pending_callback = callback

    mode.errored("other.ext")

    callback.assert_not_called()
    timer.cancel.assert_not_called()
    assert mode._loading_timer is timer


def _make_active_ext(ext_id: str) -> ExtensionRecord:
    ext = object.__new__(ExtensionRecord)
    ext.id = ext_id
    return ext


def test_started__reruns_query_for_active_extension(mocker: MockerFixture) -> None:
    from ulauncher.modes.extensions import extension_mode

    mode = _make_mode()
    mode._active_ext = _make_active_ext("test.ext")
    mocker.patch.object(extension_mode.scheduling, "run_when_idle", side_effect=lambda func: func())
    emit = mocker.patch.object(extension_mode.events, "emit")

    mode.started("test.ext")

    emit.assert_called_once_with("app:reload_query")


def test_started__ignores_other_extensions(mocker: MockerFixture) -> None:
    from ulauncher.modes.extensions import extension_mode

    mode = _make_mode()
    mode._active_ext = _make_active_ext("test.ext")
    run_when_idle = mocker.patch.object(extension_mode.scheduling, "run_when_idle")

    mode.started("other.ext")

    run_when_idle.assert_not_called()


def test_handle_response__streamed_batches_keep_callback_until_final() -> None:
    mode = _make_mode()
    callback = MagicMock()
    mode._pending_callback = callback

    non_final = effects.render_results([], append=True, final=False)
    mode._handle_response({"effect": non_final})
    assert mode._pending_callback is callback, "a non-final batch must keep the callback alive"

    final = effects.render_results([], append=True, final=True)
    mode._handle_response({"effect": final})
    assert mode._pending_callback is None, "the final batch clears the callback"

    assert callback.call_args_list == [call(non_final), call(final)]
