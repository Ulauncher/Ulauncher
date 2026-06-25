from types import SimpleNamespace

from pytest_mock import MockerFixture

from ulauncher.modes.extensions import extension_registry


def test_iterate__orders_preview_running_then_rest(mocker: MockerFixture) -> None:
    preview = SimpleNamespace(id="preview", is_preview=True, is_enabled=True, is_running=True, has_error=False)
    running = SimpleNamespace(id="running", is_preview=False, is_enabled=True, is_running=True, has_error=False)
    disabled = SimpleNamespace(id="disabled", is_preview=False, is_enabled=False, is_running=False, has_error=False)
    stopped = SimpleNamespace(id="stopped", is_preview=False, is_enabled=True, is_running=False, has_error=False)
    errored = SimpleNamespace(id="errored", is_preview=False, is_enabled=True, is_running=False, has_error=True)

    controllers = {c.id: c for c in (disabled, stopped, preview, errored, running)}
    mocker.patch.object(extension_registry.preview, "ext_id", preview.id)
    mocker.patch.object(
        extension_registry.extension_finder,
        "iterate",
        return_value=[(c.id, f"/path/{c.id}") for c in controllers.values() if not c.is_preview],
    )
    mocker.patch.object(
        extension_registry, "ExtensionController", side_effect=lambda ext_id, _path: controllers[ext_id]
    )

    assert list(extension_registry.iterate(sort=True)) == [preview, running, stopped, errored, disabled]
