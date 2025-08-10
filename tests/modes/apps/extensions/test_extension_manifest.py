from __future__ import annotations

import os

import pytest

from ulauncher.modes.extensions.extension_manifest import (
    ExtensionIncompatibleRecoverableError,
    ExtensionManifest,
    ExtensionManifestError,
)
from ulauncher.utils.json_utils import json_stringify

valid_manifest: dict[str, str | dict[str, dict[str, str]]] = {
    "api_version": "1",
    "name": "Timer",
    "authors": "Aleksandr Gornostal",
    "icon": "images/timer.png",
    "triggers": {"keyword": {"name": "Timer", "keyword": "ti"}},
}


class TestExtensionManifest:
    def test_open__manifest_file__is_read(self) -> None:
        ext_path = os.path.dirname(os.path.abspath(__file__))
        manifest = ExtensionManifest.load(f"{ext_path}/test_extension/manifest.json")
        assert manifest.name == "Test Extension"

    def test_validate__name_empty__exception_raised(self) -> None:
        manifest = ExtensionManifest({"api_version": "1"})
        with pytest.raises(ExtensionManifestError):
            manifest.validate()

    def test_validate__valid_manifest__no_exceptions_raised(self) -> None:
        manifest = ExtensionManifest(valid_manifest)
        manifest.validate()

    def test_validate__prefs_incorrect_type__exception_raised(self) -> None:
        valid_manifest["preferences"] = {"id": {"type": "incorrect"}}
        manifest = ExtensionManifest(valid_manifest)
        with pytest.raises(ExtensionManifestError):
            manifest.validate()

    def test_validate__type_kw_empty_name__exception_raised(self) -> None:
        valid_manifest["preferences"] = {"id": {"type": "incorrect", "keyword": "kw"}}
        manifest = ExtensionManifest(valid_manifest)
        with pytest.raises(ExtensionManifestError):
            manifest.validate()

    def test_validate__raises_error_if_empty_default_value_for_keyword(self) -> None:
        valid_manifest["preferences"] = {"id": {"type": "keyword", "name": "My Keyword"}}
        manifest = ExtensionManifest(valid_manifest)
        with pytest.raises(ExtensionManifestError):
            manifest.validate()

    def test_validate__doesnt_raise_if_empty_default_value_for_non_keyword(self) -> None:
        valid_manifest["preferences"] = {
            "city": {"type": "input", "name": "City"},
        }
        manifest = ExtensionManifest(valid_manifest)
        manifest.validate()

    def test_check_compatibility__manifest_version_0__exception_raised(self) -> None:
        manifest = ExtensionManifest({"name": "Test", "api_version": "0"})
        with pytest.raises(ExtensionIncompatibleRecoverableError):
            manifest.check_compatibility()

    def test_check_compatibility__api_version__no_exceptions(self) -> None:
        manifest = ExtensionManifest({"name": "Test", "api_version": "3"})
        manifest.check_compatibility()

    def test_defaults_not_included_in_stringify(self) -> None:
        # Ensure defaults don't leak
        assert json_stringify(ExtensionManifest()) == '{"input_debounce": 0.05}'
        manifest = ExtensionManifest(preferences={"ns": {"k": "v"}})
        assert json_stringify(manifest) == '{"input_debounce": 0.05, "preferences": {"ns": {"k": "v"}}}'

    def test_manifest_backwards_compatibility(self) -> None:
        em = ExtensionManifest(
            required_api_version="3",
            developer_name="John",
            manifest_version="1",
            description="asdf",
            options={"query_debounce": 0.555},
            preferences=[{"id": "asdf", "name": "ghjk"}],
        )
        assert em.get("options") is None
        assert em.get("required_api_version") is None
        assert em.get("developer_name") is None
        assert em.api_version == "3"
        assert em.authors == "John"
        assert em.input_debounce == 0.555
        asdf = em.preferences.get("asdf")
        assert asdf
        assert asdf.name == "ghjk"
