"""State-machine tests for the extension lifecycle: desired-state reconciliation and the
per-extension job queue in ExtensionService.

ExtensionRuntime is faked so the tests control when "processes" exit, which makes the
interleavings scriptable. The registry's disk/network operations (update, uninstall) are
faked at the ExtensionRegistry level with the same stop-swap-report contract as the real
chains, minus the I/O. The fakes log every step, so the tests assert the full event order.
"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import Any, Callable, Iterator

import pytest
from pytest_mock import MockerFixture

from ulauncher.modes.extensions import extension_registry, extension_service
from ulauncher.modes.extensions.extension_registry import ExtensionRegistry
from ulauncher.modes.extensions.extension_service import ExtensionService


class FakeManifest:
    triggers: dict[str, Any] = {}
    input_debounce = 0.05

    def validate(self) -> None:
        pass

    def check_compatibility(self, verbose: bool = False) -> None:
        pass

    def supports_current_api(self) -> bool:
        return True


class FakeState:
    is_enabled = True
    error_type = ""
    error_message = ""

    def save(self, **kwargs: Any) -> None:
        for key, value in kwargs.items():
            setattr(self, key, value)


class FakeRecord:
    is_preview = False

    def __init__(self, ext_id: str) -> None:
        self.id = ext_id
        self.path = f"/fake/{ext_id}"
        self.state = FakeState()
        self.manifest = FakeManifest()
        self.preferences: dict[str, Any] = {}

    @property
    def is_enabled(self) -> bool:
        return self.is_preview or (self.state.is_enabled and not self.has_error)

    @property
    def has_error(self) -> bool:
        return not self.is_preview and bool(self.state.error_type)

    def reload_state(self) -> None:
        pass


class FakePreviewRecord(FakeRecord):
    is_preview = True

    def __init__(self, ext_id: str, path: str, with_debugger: bool = False) -> None:
        super().__init__(ext_id)
        self.path = path
        self.with_debugger = with_debugger


class FakeRuntime:
    def __init__(self, ext_id: str, exit_handler: Callable[[str, str], None]) -> None:
        self.ext_id = ext_id
        self.stop_requested = False
        self._exit_handler = exit_handler

    def stop(self) -> None:
        self.stop_requested = True

    def exit(self, cause: str = "Stopped", error_msg: str = "") -> None:
        self._exit_handler(cause, error_msg)


class Harness:
    service: ExtensionService
    disk: dict[str, FakeRecord]
    spawned: list[FakeRuntime]
    log: list[str]

    def __init__(self, mocker: MockerFixture, tmp_path: Path) -> None:
        self.disk = {}
        self.spawned = []
        self.log = []
        harness = self

        def make_runtime(
            ext_id: str,
            _cmd: list[str],
            _env: dict[str, str],
            exit_handler: Callable[[str, str], None],
            _message_handler: Any,
        ) -> FakeRuntime:
            harness.log.append(f"spawn:{ext_id}")
            runtime = FakeRuntime(ext_id, exit_handler)
            harness.spawned.append(runtime)
            return runtime

        # The registry fakes mirror the real chains' contract: stop through the lifecycle,
        # do the disk work, report. The real service.stop_extension decides whether a previewed
        # id actually needs stopping.

        def fake_update(service: Any, record: Any, on_success: Callable[[bool], None], _on_error: Any) -> None:
            harness.log.append(f"update-start:{record.id}")

            def swap() -> None:
                harness.log.append(f"update-swap:{record.id}")
                on_success(True)

            service.stop_extension(record, swap)

        def fake_uninstall(service: Any, record: Any, on_done: Callable[[], None], _on_error: Any) -> None:
            def remove() -> None:
                harness.log.append(f"uninstall-remove:{record.id}")
                del harness.disk[record.id]
                on_done()

            service.stop_extension(record, remove)

        mocker.patch.object(extension_service, "ExtensionRuntime", make_runtime)
        mocker.patch.object(extension_service, "PreviewExtensionRecord", FakePreviewRecord)
        mocker.patch.object(extension_service.cli, "get_args", return_value=SimpleNamespace(verbose=False))
        mocker.patch.object(
            extension_registry.extension_finder,
            "locate",
            side_effect=lambda ext_id: self.disk[ext_id].path if ext_id in self.disk else None,
        )
        mocker.patch.object(extension_registry, "ExtensionRecord", side_effect=lambda ext_id, _path: self.disk[ext_id])
        mocker.patch.object(ExtensionRegistry, "update", fake_update)
        mocker.patch.object(ExtensionRegistry, "uninstall", fake_uninstall)
        # redirect the preview log off the real state dir so its file writes land in tmp_path
        mocker.patch.object(extension_service.paths, "PREVIEW_LOG_FILE", str(tmp_path / "preview.log"))
        self.service = ExtensionService()

    def add_installed(self, ext_id: str) -> Any:
        record = FakeRecord(ext_id)
        self.disk[ext_id] = record
        return record

    def start(self, record: Any) -> FakeRuntime:
        self.service.start_extension(record)
        return self.spawned[-1]


@pytest.fixture
def harness(mocker: MockerFixture, tmp_path: Path) -> Iterator[Harness]:
    yield Harness(mocker, tmp_path)
    # rebind the event bus to the module singleton; the harness service took over the binding
    extension_service.events.set_self(extension_service.ext_service)


def unexpected_error(error: Exception) -> None:
    pytest.fail(f"Unexpected error reported: {error}")


def test_update_then_uninstall_runs_in_order_and_does_not_resurrect(harness: Harness) -> None:
    record = harness.add_installed("ext")
    runtime = harness.start(record)
    results: list[Any] = []

    harness.service.update(record, lambda updated: results.append(("updated", updated)), unexpected_error)
    harness.service.uninstall(record, lambda: results.append("removed"), unexpected_error)

    # the update job holds the id: it has requested the stop, the uninstall is queued behind it
    assert runtime.stop_requested
    assert "uninstall-remove:ext" not in harness.log

    runtime.exit("Stopped")

    assert results == [("updated", True), "removed"]
    # the swap lands before the removal, and the final reconcile finds no record:
    # nothing respawns and no error state is written
    assert harness.log == ["spawn:ext", "update-start:ext", "update-swap:ext", "uninstall-remove:ext"]
    assert record.state.error_type == ""


def test_update_queued_behind_uninstall_is_dropped(harness: Harness) -> None:
    record = harness.add_installed("ext")
    runtime = harness.start(record)
    results: list[Any] = []

    harness.service.uninstall(record, lambda: results.append("removed"), unexpected_error)
    harness.service.update(
        record,
        lambda updated: results.append(("updated", updated)),
        lambda error: results.append(("error", error)),
    )

    # the uninstall job holds the id: it has requested the stop, the update is queued behind it
    assert runtime.stop_requested
    assert "update-start:ext" not in harness.log

    runtime.exit("Stopped")

    # the uninstall runs to completion; the queued update re-resolves the record, finds it
    # gone, and is dropped rather than resurrecting the extension
    assert results[0] == "removed"
    assert results[1][0] == "error"
    assert "update-start:ext" not in harness.log
    assert "ext" not in harness.disk


def test_disable_update_enable_starts_the_new_version_last(harness: Harness) -> None:
    record = harness.add_installed("ext")
    runtime = harness.start(record)

    harness.service.toggle_enabled(record, False)
    assert runtime.stop_requested

    harness.service.update(record, lambda _updated: None, unexpected_error)
    harness.service.toggle_enabled(record, True)
    # the update job still holds the id, so enabling must not start anything yet
    assert len(harness.spawned) == 1

    runtime.exit("Stopped")

    # the swap completed before the job's reconcile started the extension again
    assert harness.log == ["spawn:ext", "update-start:ext", "update-swap:ext", "spawn:ext"]


def test_concurrent_updates_of_one_id_serialize(harness: Harness) -> None:
    record = harness.add_installed("ext")
    runtime = harness.start(record)

    harness.service.update(record, lambda _updated: None, unexpected_error)
    harness.service.update(record, lambda _updated: None, unexpected_error)
    # the second update is queued, not started
    assert harness.log.count("update-start:ext") == 1

    runtime.exit("Stopped")

    # the updates ran back to back, with one restart at the end instead of one per update
    assert harness.log == [
        "spawn:ext",
        "update-start:ext",
        "update-swap:ext",
        "update-start:ext",
        "update-swap:ext",
        "spawn:ext",
    ]


def test_disabling_during_update_leaves_it_stopped(harness: Harness) -> None:
    record = harness.add_installed("ext")
    runtime = harness.start(record)

    harness.service.update(record, lambda _updated: None, unexpected_error)
    harness.service.toggle_enabled(record, False)
    runtime.exit("Stopped")

    assert "update-swap:ext" in harness.log
    assert len(harness.spawned) == 1
    assert not harness.service.is_running(record)


def test_crash_does_not_restart(harness: Harness) -> None:
    record = harness.add_installed("ext")
    runtime = harness.start(record)

    runtime.exit("Exited", "boom")

    assert record.state.error_type == "Exited"
    assert len(harness.spawned) == 1
    assert not harness.service.is_running(record)


def test_stop_during_stop_waits_for_the_same_exit(harness: Harness) -> None:
    record = harness.add_installed("ext")
    runtime = harness.start(record)
    stopped: list[str] = []

    harness.service.stop_extension(record, lambda: stopped.append("first"))
    harness.service.stop_extension(record, lambda: stopped.append("second"))
    assert stopped == []

    runtime.exit("Stopped")
    assert stopped == ["first", "second"]


def test_preview_crash_during_a_pending_stop_does_not_respawn_the_preview(harness: Harness) -> None:
    record = harness.add_installed("ext")
    runtime = harness.start(record)

    harness.service.preview_ext("ext", "/dev/ext")
    runtime.exit("Stopped")
    preview_runtime = harness.spawned[-1]

    # A restart registers a stop callback for the preview's exit. The exit can still arrive
    # classified as a crash: ExtensionRuntime.stop() gives up without marking the subprocess as
    # aborted when Gio has already reaped it, so the exit is reported as an error.
    harness.service.reload(["ext"])
    assert preview_runtime.stop_requested
    preview_runtime.exit("Exited", "boom")

    # The overlay is gone and the installed extension took over. A reconcile that ran before
    # stop_preview cleared the overlay would have respawned the dead preview first.
    assert harness.service.preview is None
    assert len(harness.spawned) == 3
    assert not harness.spawned[-1].stop_requested


def test_update_during_preview_keeps_preview_running_until_stop_preview(harness: Harness) -> None:
    record = harness.add_installed("ext")
    runtime = harness.start(record)

    harness.service.preview_ext("ext", "/dev/ext")
    assert runtime.stop_requested
    runtime.exit("Stopped")

    # the reconcile after the restart job launched the preview
    preview_runtime = harness.spawned[-1]
    assert len(harness.spawned) == 2

    harness.service.update(record, lambda _updated: None, unexpected_error)
    # the update swapped the installed files but did not touch the running preview
    assert not preview_runtime.stop_requested
    assert len(harness.spawned) == 2

    harness.service.stop_preview()
    assert preview_runtime.stop_requested
    preview_runtime.exit("Stopped")

    # only after stop_preview does the updated installed version start
    assert harness.log == ["spawn:ext", "spawn:ext", "update-start:ext", "update-swap:ext", "spawn:ext"]
