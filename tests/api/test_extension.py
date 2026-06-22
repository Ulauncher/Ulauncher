from __future__ import annotations

import logging
import os
from typing import TYPE_CHECKING, Iterator
from unittest.mock import patch

import pytest
from pytest_mock import MockerFixture

from ulauncher.api import extension as extension_module
from ulauncher.api.extension import Extension
from ulauncher.internals.result import Result

if TYPE_CHECKING:
    from ulauncher.internals import ipc

_INPUT_EVENT: ipc.Event = {"type": "event:input_trigger", "args": ("", "t")}


class TestExtension:
    def test_init__verbose_env_controls_log_level(self, mocker: MockerFixture) -> None:
        mocker.patch("ulauncher.api.extension.Client")
        basic_config = mocker.patch("ulauncher.api.extension.logging.basicConfig")
        mocker.patch("ulauncher.api.extension.signal.signal")

        with patch.dict(os.environ, {"ULAUNCHER_EXTENSION_ID": "com.example.test", "VERBOSE": "0"}):
            Extension()

        assert basic_config.call_args_list[0].kwargs["level"] == logging.WARNING

        basic_config.reset_mock()

        with patch.dict(os.environ, {"ULAUNCHER_EXTENSION_ID": "com.example.test", "VERBOSE": "1"}):
            Extension()

        assert basic_config.call_args_list[0].kwargs["level"] == logging.DEBUG


def _batches(ext: Extension) -> list[tuple[bool, bool, list[str], list[int]]]:
    """(append, final, result names, result ids) for each render the extension sent."""
    batches = []
    for call in ext._client.send.call_args_list:  # type: ignore[attr-defined]
        effect = call.args[0]["response"]["effect"]
        results = effect["results"]
        names = [r["name"] for r in results]
        ids = [r["__result_id__"] for r in results]
        batches.append((effect["append"], effect["final"], names, ids))
    return batches


class TestStreamingResponses:
    @pytest.fixture
    def ext(self, mocker: MockerFixture) -> Extension:
        mocker.patch("ulauncher.api.extension.Client")
        mocker.patch("ulauncher.api.extension.signal.signal")
        # run scheduled responses synchronously so we can assert on them inline
        mocker.patch.object(extension_module.scheduling, "run_when_idle", side_effect=lambda fn, *a: fn(*a))
        with patch.dict(os.environ, {"ULAUNCHER_EXTENSION_ID": "com.example.test"}):
            return Extension()

    def test_yielding_results_appends_with_continuous_ids(self, ext: Extension) -> None:
        def gen() -> Iterator[Result]:
            yield Result(name="a")
            yield Result(name="b")

        ext.run_event_listener(1, _INPUT_EVENT, gen, ())
        assert _batches(ext) == [
            (True, False, ["a"], [0]),
            (True, False, ["b"], [1]),
            (True, True, [], []),
        ]

    def test_yielding_lists_replaces_but_keeps_ids_unique(self, ext: Extension) -> None:
        def gen() -> Iterator[list[Result]]:
            yield [Result(name="a")]
            yield [Result(name="a"), Result(name="b")]

        ext.run_event_listener(1, _INPUT_EVENT, gen, ())
        assert _batches(ext) == [
            (False, False, ["a"], [0]),
            (False, False, ["a", "b"], [1, 2]),
            (True, True, [], []),
        ]

    def test_empty_generator_sends_final_empty_replace(self, ext: Extension) -> None:
        def gen() -> Iterator[Result]:
            return
            yield  # makes this a generator

        ext.run_event_listener(1, _INPUT_EVENT, gen, ())
        assert _batches(ext) == [(False, True, [], [])]

    def test_returned_list_is_a_single_final_response(self, ext: Extension) -> None:
        ext.run_event_listener(1, _INPUT_EVENT, lambda: [Result(name="a")], ())
        assert _batches(ext) == [(False, True, ["a"], [0])]

    def test_stale_generator_stops_without_sending(self, ext: Extension) -> None:
        ext._input_request_id = 5

        def gen() -> Iterator[Result]:
            yield Result(name="a")
            yield Result(name="b")

        ext.run_event_listener(1, _INPUT_EVENT, gen, (), input_request_id=4)  # superseded by 5
        assert _batches(ext) == []
