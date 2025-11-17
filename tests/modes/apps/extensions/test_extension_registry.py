from types import SimpleNamespace

from pytest_mock import MockerFixture

from ulauncher.modes.extensions import extension_registry


def test_iterate__orders_preview_running_then_rest(mocker: MockerFixture) -> None:
    preview = SimpleNamespace(id="preview", is_preview=True, is_enabled=True, is_running=True, has_error=False)
    running = SimpleNamespace(id="running", is_preview=False, is_enabled=True, is_running=True, has_error=False)
    disabled = SimpleNamespace(id="disabled", is_preview=False, is_enabled=False, is_running=False, has_error=False)
    stopped = SimpleNamespace(id="stopped", is_preview=False, is_enabled=True, is_running=False, has_error=False)
    errored = SimpleNamespace(id="errored", is_preview=False, is_enabled=True, is_running=False, has_error=True)

    controllers = {
        disabled.id: disabled,
        stopped.id: stopped,
        preview.id: preview,
        errored.id: errored,
        running.id: running,
    }
    mocker.patch.object(extension_registry, "_ext_controllers", controllers)

    assert list(extension_registry.iterate()) == [preview, running, stopped, errored, disabled]
