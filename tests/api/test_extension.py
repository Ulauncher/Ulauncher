from __future__ import annotations

import logging
import os
from typing import Any, Iterator
from unittest.mock import MagicMock, patch

from pytest_mock import MockerFixture

from ulauncher.api.extension import Extension
from ulauncher.internals.result import Result


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


class TestExtensionPartialResponses:
    def _make_extension(self, mocker: MockerFixture, env: dict[str, str]) -> Extension:
        mocker.patch("ulauncher.api.extension.Client")
        mocker.patch("ulauncher.api.extension.logging.basicConfig")
        mocker.patch("ulauncher.api.extension.signal.signal")
        # Run idle callbacks synchronously so client.send calls can be asserted directly
        mocker.patch("ulauncher.api.extension.GLib.idle_add", side_effect=lambda fn, *args: fn(*args))

        with patch.dict(os.environ, {"ULAUNCHER_EXTENSION_ID": "com.example.test", **env}):
            return Extension()

    def _sent_responses(self, extension: Extension) -> list[dict[str, Any]]:
        send_mock = extension._client.send  # type: ignore[attr-defined]
        assert isinstance(send_mock, MagicMock)
        return [call.args[1] for call in send_mock.call_args_list if call.args[0] == "response"]

    def test_generator_streams_partials_when_supported(self, mocker: MockerFixture) -> None:
        extension = self._make_extension(
            mocker, {"ULAUNCHER_PARTIAL_RESPONSES": "1", "ULAUNCHER_PARTIAL_RESPONSE_INTERVAL": "0"}
        )
        results = [Result(name=f"item{i}") for i in range(3)]

        def listener(_query: str) -> Iterator[Result]:
            yield from results

        extension.run_event_listener({"type": "event:input_trigger"}, listener, ("query",), input_request_id=0)

        responses = self._sent_responses(extension)
        assert len(responses) == 4, "expected one partial per result plus the final response"
        assert all(response.get("partial") for response in responses[:3])
        assert "partial" not in responses[3]
        assert [len(response["effect"]) for response in responses] == [1, 2, 3, 3]

    def test_generator_is_collected_without_capability_flag(self, mocker: MockerFixture) -> None:
        extension = self._make_extension(mocker, {})

        def listener(_query: str) -> Iterator[Result]:
            yield from (Result(name=f"item{i}") for i in range(3))

        extension.run_event_listener({"type": "event:input_trigger"}, listener, ("query",), input_request_id=0)

        responses = self._sent_responses(extension)
        assert len(responses) == 1, "without the capability flag the generator must be collected"
        assert "partial" not in responses[0]
        assert len(responses[0]["effect"]) == 3

    def test_partials_are_throttled(self, mocker: MockerFixture) -> None:
        extension = self._make_extension(
            mocker, {"ULAUNCHER_PARTIAL_RESPONSES": "1", "ULAUNCHER_PARTIAL_RESPONSE_INTERVAL": "1000"}
        )

        def listener(_query: str) -> Iterator[Result]:
            yield from (Result(name=f"item{i}") for i in range(10))

        extension.run_event_listener({"type": "event:input_trigger"}, listener, ("query",), input_request_id=0)

        responses = self._sent_responses(extension)
        assert len(responses) == 2, "expected the leading partial and the final response only"
        assert responses[0].get("partial")
        assert "partial" not in responses[1]
        assert len(responses[1]["effect"]) == 10

    def test_yielded_lists_replace_accumulated_results(self, mocker: MockerFixture) -> None:
        extension = self._make_extension(
            mocker, {"ULAUNCHER_PARTIAL_RESPONSES": "1", "ULAUNCHER_PARTIAL_RESPONSE_INTERVAL": "0"}
        )

        def listener(_query: str) -> Iterator[Result | list[Result]]:
            yield [Result(name="answer: hello")]
            yield [Result(name="answer: hello world!")]
            yield Result(name="extra item")

        extension.run_event_listener({"type": "event:input_trigger"}, listener, ("query",), input_request_id=0)

        responses = self._sent_responses(extension)
        assert [len(response["effect"]) for response in responses] == [1, 1, 2, 2]
        assert responses[1]["effect"][0]["name"] == "answer: hello world!"
        assert responses[3]["effect"][1]["name"] == "extra item"

    def test_failing_generator_still_sends_a_final_response(self, mocker: MockerFixture) -> None:
        extension = self._make_extension(
            mocker, {"ULAUNCHER_PARTIAL_RESPONSES": "1", "ULAUNCHER_PARTIAL_RESPONSE_INTERVAL": "1000"}
        )

        def listener(_query: str) -> Iterator[Result]:
            yield Result(name="item0")
            msg = "boom"
            raise RuntimeError(msg)

        extension.run_event_listener({"type": "event:input_trigger"}, listener, ("query",), input_request_id=0)

        responses = self._sent_responses(extension)
        assert "partial" not in responses[-1], "the app must always receive a final response"
        assert len(responses[-1]["effect"]) == 1

    def test_superseded_request_stops_consuming_the_generator(self, mocker: MockerFixture) -> None:
        extension = self._make_extension(
            mocker, {"ULAUNCHER_PARTIAL_RESPONSES": "1", "ULAUNCHER_PARTIAL_RESPONSE_INTERVAL": "0"}
        )
        consumed: list[str] = []

        def listener(_query: str) -> Iterator[Result]:
            consumed.append("first")
            yield Result(name="first")
            extension._input_request_id += 1  # a newer input arrived mid-stream
            consumed.append("second")
            yield Result(name="second")
            consumed.append("third")
            yield Result(name="third")

        extension.run_event_listener({"type": "event:input_trigger"}, listener, ("query",), input_request_id=0)

        assert consumed == ["first", "second"], "iteration must stop once the request is superseded"
        responses = self._sent_responses(extension)
        assert len(responses) == 1
        assert responses[0].get("partial")
        assert len(responses[0]["effect"]) == 1, "no final response must be sent for a superseded request"
