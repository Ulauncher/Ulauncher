from types import SimpleNamespace

from pytest_mock import MockerFixture

from ulauncher.modes.extensions import extension_registry


def test_iterate__orders_preview_running_then_rest(mocker: MockerFixture) -> None:
    preview = SimpleNamespace(id="preview", is_preview=True, is_running=True)
    running = SimpleNamespace(id="running", is_preview=False, is_running=True)
    stopped = SimpleNamespace(id="stopped", is_preview=False, is_running=False)
    errored = SimpleNamespace(id="errored", is_preview=False, is_running=False)

    controllers = {
        stopped.id: stopped,
        preview.id: preview,
        running.id: running,
        errored.id: errored,
    }
    mocker.patch.object(extension_registry, "_ext_controllers", controllers)

    assert list(extension_registry.iterate()) == [preview, running, stopped, errored]
