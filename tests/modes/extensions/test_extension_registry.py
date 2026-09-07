from types import SimpleNamespace
from typing import Any

from pytest_mock import MockerFixture

from ulauncher import paths
from ulauncher.internals.install_source import InstallSource
from ulauncher.modes.extensions import ext_exceptions, extension_registry
from ulauncher.modes.extensions.extension_manifest import ExtensionManifest
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


def test_install_from_staging__rejects_theme_tree(tmp_path: Any, monkeypatch: Any) -> None:
    """A theme URL pasted into the extension installer fails naming the kind, and swaps nothing in."""
    staged = tmp_path / "staged-theme"
    staged.mkdir()
    (staged / "manifest.json").write_text('{"name": "x", "css_file": "theme.css"}')
    (staged / "theme.css").write_text(".app {}")
    monkeypatch.setattr(paths, "USER_EXTENSIONS", str(tmp_path / "extensions"))

    installed: list[Any] = []
    errors: list[Exception] = []
    source = InstallSource("https://example.com/user/repo")
    ExtensionRegistry().install_from_staging(source, str(staged), "abc", 1700000000.0, installed.append, errors.append)
    assert installed == []
    assert len(errors) == 1
    assert "is a theme, not an extension" in str(errors[0])
    assert not (tmp_path / "extensions").exists()


def test_install_from_staging__rejects_api_incompatible_extension(tmp_path: Any, monkeypatch: Any) -> None:
    """An extension too new for the API is rejected before anything is swapped in."""
    staged = tmp_path / "staged-incompatible"
    staged.mkdir()
    (staged / "manifest.json").write_text('{"name": "x", "api_version": "4"}')
    monkeypatch.setattr(paths, "USER_EXTENSIONS", str(tmp_path / "extensions"))

    installed: list[Any] = []
    errors: list[Exception] = []
    ExtensionRegistry().install_from_staging(
        InstallSource("https://example.com/user/repo"),
        str(staged),
        "abc",
        1700000000.0,
        installed.append,
        errors.append,
    )
    assert installed == []
    assert len(errors) == 1
    assert isinstance(errors[0], ext_exceptions.CompatibilityError)
    assert not (tmp_path / "extensions").exists()


def test_install_from_staging__rereads_manifest_after_earlier_load(tmp_path: Any, monkeypatch: Any) -> None:
    """Reinstall/update in one process must re-read the staged manifest, not reuse the cached one.

    The staging path is fixed per extension, so an earlier install with a compatible manifest
    would otherwise let a later incompatible update past the API gate.
    """
    staged = tmp_path / "staged-ext"
    staged.mkdir()
    (staged / "manifest.json").write_text('{"name": "x", "api_version": "3"}')
    monkeypatch.setattr(paths, "USER_EXTENSIONS", str(tmp_path / "extensions"))

    # Cache the compatible manifest for this staging path, as a prior install would
    ExtensionManifest.load(str(staged))
    (staged / "manifest.json").write_text('{"name": "x", "api_version": "4"}')

    installed: list[Any] = []
    errors: list[Exception] = []
    ExtensionRegistry().install_from_staging(
        InstallSource("https://example.com/user/repo"),
        str(staged),
        "abc",
        1700000000.0,
        installed.append,
        errors.append,
    )
    assert installed == []
    assert len(errors) == 1
    assert isinstance(errors[0], ext_exceptions.CompatibilityError)
