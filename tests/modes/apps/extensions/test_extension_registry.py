from types import SimpleNamespace

from pytest_mock import MockerFixture

from ulauncher.modes.extensions import extension_registry


def test_iterate__orders_preview_enabled_error_disabled(mocker: MockerFixture) -> None:
    preview = SimpleNamespace(id="preview", is_preview=True, is_enabled=True, has_error=False)
    enabled = SimpleNamespace(id="enabled", is_preview=False, is_enabled=True, has_error=False)
    errored = SimpleNamespace(id="errored", is_preview=False, is_enabled=True, has_error=True)
    disabled = SimpleNamespace(id="disabled", is_preview=False, is_enabled=False, has_error=False)

    controllers = {c.id: c for c in (disabled, errored, preview, enabled)}
    mocker.patch.object(extension_registry.preview, "ext_id", preview.id)
    mocker.patch.object(
        extension_registry.extension_finder,
        "iterate",
        return_value=[(c.id, f"/path/{c.id}") for c in controllers.values() if not c.is_preview],
    )
    mocker.patch.object(
        extension_registry, "ExtensionController", side_effect=lambda ext_id, _path: controllers[ext_id]
    )

    assert list(extension_registry.iterate(sort=True)) == [preview, enabled, errored, disabled]
