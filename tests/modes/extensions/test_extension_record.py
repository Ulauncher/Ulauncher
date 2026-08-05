from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from ulauncher.modes.extensions import ext_exceptions
from ulauncher.modes.extensions.extension_record import ExtensionErrorData, ExtensionRecord


def test_seed_default_state__applies_the_bundled_defaults(tmp_path: Path) -> None:
    (tmp_path / ".default-state.json").write_text(json.dumps({"is_enabled": False, "url": "https://example.com"}))
    record = ExtensionRecord("test_record_seeds_defaults", str(tmp_path))

    assert record.state.is_enabled is False
    assert record.state.url == "https://example.com"


def test_seed_default_state__ignores_keys_the_state_rejects(tmp_path: Path) -> None:
    (tmp_path / ".default-state.json").write_text(json.dumps({"is_enabled": False, "save": "shadows a method"}))
    record = ExtensionRecord("test_record_ignores_rejected_defaults", str(tmp_path))

    assert record.state.is_enabled is False
    assert "save" not in record.state


def test_reload_state__resets_to_the_defaults_when_the_file_is_gone(tmp_path: Path) -> None:
    (tmp_path / ".default-state.json").write_text(json.dumps({"url": "https://example.com"}))
    record = ExtensionRecord("test_record_reloads_deleted_state", str(tmp_path))
    record.state.save(is_enabled=False, error=ExtensionErrorData(type="Terminated"))
    record._state_path.unlink()

    record.reload_state()

    assert record.state.is_enabled is True
    assert record.state.error is None
    assert record.state.url == "https://example.com"


INSTALL_URL = "https://host.tld/user/repo"
MOVED_URL = "https://newhost.tld/user/repo"
TRACKER_URL = "https://tracker.tld/user/repo/-/issues"


def record_with_manifest(ext_id: str, path: Path, manifest: dict[str, Any] | None = None) -> ExtensionRecord:
    if manifest is not None:
        (path / "manifest.json").write_text(json.dumps(manifest))
    record = ExtensionRecord(ext_id, str(path))
    record.state.url = INSTALL_URL
    return record


@pytest.mark.parametrize(
    ("case", "manifest", "browser_url", "expected"),
    [
        ("declared_wins", {"urls": {"website": MOVED_URL}}, INSTALL_URL, MOVED_URL),
        ("falls_back_to_derived", None, INSTALL_URL, INSTALL_URL),
        ("non_http_is_dropped", None, "file:///home/user/repo", ""),
        ("invalid_declared_falls_back", {"urls": {"website": "file:///home/user/repo"}}, INSTALL_URL, INSTALL_URL),
    ],
)
def test_website_url(
    case: str, manifest: dict[str, Any] | None, browser_url: str, expected: str, tmp_path: Path
) -> None:
    record = record_with_manifest(f"test_record_website_{case}", tmp_path, manifest)
    record.state.browser_url = browser_url

    assert record.website_url == expected


@pytest.mark.parametrize(
    ("case", "manifest", "expected"),
    [
        ("declared", {"urls": {"issues": TRACKER_URL}}, TRACKER_URL),
        ("not_declared", {"urls": {"website": INSTALL_URL}}, ""),
    ],
)
def test_issues_url(case: str, manifest: dict[str, Any], expected: str, tmp_path: Path) -> None:
    record = record_with_manifest(f"test_record_issues_{case}", tmp_path, manifest)

    assert record.issues_url == expected


@pytest.mark.parametrize(
    ("case", "manifest", "expected"),
    [
        ("no_declared_remote", None, INSTALL_URL),
        ("declared_remote", {"urls": {"remote": MOVED_URL}}, MOVED_URL),
        ("non_http_remote", {"urls": {"remote": "file:///etc"}}, INSTALL_URL),
        ("unreadable_manifest", {"triggers": "not an object"}, INSTALL_URL),
    ],
)
def test_update_url(case: str, manifest: dict[str, Any] | None, expected: str, tmp_path: Path) -> None:
    record = record_with_manifest(f"test_record_update_{case}", tmp_path, manifest)

    assert record.update_url == expected


def test_display_manifest__unreadable__falls_back_without_raising(tmp_path: Path) -> None:
    ext_id = "test_record_display_manifest_unreadable"
    record = record_with_manifest(ext_id, tmp_path, {"triggers": "not an object"})
    record.state.browser_url = INSTALL_URL

    with pytest.raises(ext_exceptions.ManifestError):
        _ = record.manifest

    # Every display path degrades instead of taking the preferences window down with it
    assert record.display_manifest.name == ext_id
    assert record.preferences == {}
    assert record.triggers == {}
    assert record.get_icon_value() == ""
    assert record.website_url == INSTALL_URL
    assert record.issues_url == ""
