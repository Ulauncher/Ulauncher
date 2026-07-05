from types import SimpleNamespace
from typing import Any

from pytest_mock import MockerFixture

from ulauncher.modes.extensions import extension_registry
from ulauncher.modes.extensions.extension_registry import ExtensionRegistry


def test_iterate__orders_preview_enabled_error_disabled(mocker: MockerFixture) -> None:
    preview: Any = SimpleNamespace(id="preview", is_preview=True, is_enabled=True, has_error=False)
    enabled = SimpleNamespace(id="enabled", is_preview=False, is_enabled=True, has_error=False)
    errored = SimpleNamespace(id="errored", is_preview=False, is_enabled=True, has_error=True)
    disabled = SimpleNamespace(id="disabled", is_preview=False, is_enabled=False, has_error=False)

    records = {c.id: c for c in (disabled, errored, preview, enabled)}
    mocker.patch.object(
        extension_registry.extension_finder,
        "iterate",
        return_value=[(c.id, f"/path/{c.id}") for c in records.values() if not c.is_preview],
    )
    # Mock ExtensionRecord to return our predefined record objects instead of real records
    mocker.patch.object(
        extension_registry,
        "ExtensionRecord",
        side_effect=lambda ext_id, _path: records[ext_id],
    )

    registry = ExtensionRegistry()
    registry.preview = preview

    assert list(registry.iterate(sort=True)) == [preview, enabled, errored, disabled]
