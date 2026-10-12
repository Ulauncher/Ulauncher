from __future__ import annotations

from types import SimpleNamespace
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, call

from pytest_mock import MockerFixture

from ulauncher.internals import effects
from ulauncher.internals.query import Query
from ulauncher.internals.result import Result
from ulauncher.modes.extensions.extension_record import ExtensionRecord, ExtensionRecordTrigger

if TYPE_CHECKING:
    from ulauncher.modes.extensions.extension_mode import ExtensionMode


def _make_mode() -> tuple[ExtensionMode, MagicMock]:
    from ulauncher.modes.extensions import extension_mode

    service = MagicMock()
    return extension_mode.ExtensionMode(service), service


def test_handle_query__transitioning_extension_waits(mocker: MockerFixture) -> None:
    from ulauncher.modes.extensions import extension_mode

    mode, service = _make_mode()
    mode._trigger_cache = {"kw": ("trigger1", "test.ext")}
    ext = SimpleNamespace(id="test.ext")
    service.get.return_value = ext
    service.is_running.return_value = False
    timer = mocker.patch.object(extension_mode.scheduling, "timer", return_value=MagicMock())
    callback = MagicMock()

    mode.handle_query(Query("kw", "arg"), callback)

    callback.assert_not_called()
    timer.assert_called_once()
    assert mode._active_ext is ext


def test_handle_query__loading_timeout_shows_empty(mocker: MockerFixture) -> None:
    from ulauncher.modes.extensions import extension_mode

    mode, service = _make_mode()
    mode._trigger_cache = {"kw": ("trigger1", "test.ext")}
    ext = SimpleNamespace(id="test.ext")
    service.get.return_value = ext
    service.is_running.return_value = False
    timer = mocker.patch.object(extension_mode.scheduling, "timer", return_value=MagicMock())
    callback = MagicMock()

    mode.handle_query(Query("kw", "arg"), callback)
    timer.call_args.args[1]()  # fire the captured loading-timeout callback

    callback.assert_called_once_with(effects.render_results([]))
    assert mode._loading_timer is None


def test_handle_query__unknown_keyword_shows_message() -> None:
    mode, service = _make_mode()
    service.iterate.return_value = iter([])
    service.get.return_value = None
    callback = MagicMock()

    mode.handle_query(Query("kw", "arg"), callback)

    callback.assert_called_once()
    (effect,) = callback.call_args.args
    assert [r.name for r in effect["results"]] == ["Extension not available"]


def test_errored__while_loading_shows_failure(mocker: MockerFixture) -> None:
    mode, _service = _make_mode()
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
    mode, _service = _make_mode()
    mode._active_ext = _make_active_ext("test.ext")
    callback = MagicMock()
    mode._pending_callback = callback

    mode.errored("test.ext")

    callback.assert_not_called()
    assert mode._pending_callback is None


def test_errored__ignores_other_extensions() -> None:
    mode, _service = _make_mode()
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

    mode, _service = _make_mode()
    mode._active_ext = _make_active_ext("test.ext")
    mocker.patch.object(extension_mode.scheduling, "run_when_idle", side_effect=lambda func: func())
    emit = mocker.patch.object(extension_mode.events, "emit")

    mode.started("test.ext")

    emit.assert_called_once_with("app:reload_query")


def test_started__ignores_other_extensions(mocker: MockerFixture) -> None:
    from ulauncher.modes.extensions import extension_mode

    mode, _service = _make_mode()
    mode._active_ext = _make_active_ext("test.ext")
    run_when_idle = mocker.patch.object(extension_mode.scheduling, "run_when_idle")

    mode.started("other.ext")

    run_when_idle.assert_not_called()


def test_handle_response__streamed_batches_keep_callback_until_final() -> None:
    mode, _service = _make_mode()
    callback = MagicMock()
    mode._pending_callback = callback

    non_final = effects.render_results([], append=True, final=False)
    mode._handle_response({"effect": non_final})
    assert mode._pending_callback is callback, "a non-final batch must keep the callback alive"

    final = effects.render_results([], append=True, final=True)
    mode._handle_response({"effect": final})
    assert mode._pending_callback is None, "the final batch clears the callback"

    assert callback.call_args_list == [call(non_final), call(final)]


def _make_ext_with_triggers() -> MagicMock:
    return MagicMock(
        id="test.ext",
        triggers={
            "main": ExtensionRecordTrigger(default_keyword="kw", keyword="userkw"),
            "other": ExtensionRecordTrigger(default_keyword="other", keyword="other"),
            "launcher": ExtensionRecordTrigger(),
        },
    )


def test_handle_message__trigger_query_gets_user_keyword() -> None:
    mode, _service = _make_mode()
    mode._active_ext = _make_ext_with_triggers()
    mode._request_id = 1
    callback = MagicMock()
    mode._pending_callback = callback

    mode.handle_message(
        "test.ext", {"name": "response", "request_id": 1, "response": {"effect": effects.set_query("arg", "main")}}
    )

    callback.assert_called_once_with(effects.set_query("userkw arg"))


def test_resolve_queries__trigger_without_keyword_does_nothing() -> None:
    mode, _service = _make_mode()
    ext = _make_ext_with_triggers()

    assert mode._resolve_queries(ext, effects.set_query("arg", "launcher")) == effects.do_nothing()
    assert mode._resolve_queries(ext, effects.set_query("arg", "missing")) == effects.do_nothing()


def test_resolve_queries__whole_query_with_default_keyword_gets_user_keyword() -> None:
    mode, _service = _make_mode()
    ext = _make_ext_with_triggers()

    assert mode._resolve_queries(ext, effects.set_query("kw arg")) == effects.set_query("userkw arg")
    assert mode._resolve_queries(ext, effects.set_query("userkw arg")) == effects.set_query("userkw arg")
    assert mode._resolve_queries(ext, effects.set_query("unrelated arg")) == effects.set_query("unrelated arg")


def test_resolve_queries__resolves_nested_effects() -> None:
    mode, _service = _make_mode()
    ext = _make_ext_with_triggers()
    run_many: effects.LegacyRunMany = {
        "type": effects.EffectType.LEGACY_RUN_MANY,
        "effects": [effects.set_query("arg", "other")],
    }

    assert mode._resolve_queries(ext, run_many) == {
        "type": effects.EffectType.LEGACY_RUN_MANY,
        "effects": [effects.set_query("other arg")],
    }
