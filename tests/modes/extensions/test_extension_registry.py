from types import SimpleNamespace

from pytest_mock import MockerFixture

from ulauncher.modes.extensions import extension_registry
from ulauncher.modes.extensions.extension_controller import PreviewExtensionController


def test_iterate__orders_preview_enabled_error_disabled(mocker: MockerFixture) -> None:
    preview = PreviewExtensionController(ext_id="preview", path="/path/preview")
    enabled = SimpleNamespace(id="enabled", is_preview=False, is_enabled=True, has_error=False)
    errored = SimpleNamespace(id="errored", is_preview=False, is_enabled=True, has_error=True)
    disabled = SimpleNamespace(id="disabled", is_preview=False, is_enabled=False, has_error=False)

    controllers = {c.id: c for c in (disabled, errored, enabled)}
    mocker.patch.object(extension_registry.ext_service, "_preview", preview)
    mocker.patch.object(
        extension_registry.extension_finder,
        "iterate",
        return_value=[(c.id, f"/path/{c.id}") for c in controllers.values()],
    )
    mocker.patch.object(
        extension_registry, "ExtensionController", side_effect=lambda ext_id, _path: controllers[ext_id]
    )

    assert list(extension_registry.iterate(sort=True)) == [preview, enabled, errored, disabled]
