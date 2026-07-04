from __future__ import annotations

import os
from typing import Any

import pytest

from ulauncher.modes.extensions import ext_exceptions
from ulauncher.modes.extensions.extension_manifest import ExtensionManifest
from ulauncher.utils.json_utils import json_stringify

valid_manifest: dict[str, Any] = {
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
        with pytest.raises(ext_exceptions.ManifestError):
            manifest.validate()

    def test_validate__valid_manifest__no_exceptions_raised(self) -> None:
        manifest = ExtensionManifest(valid_manifest)
        manifest.validate()

    def test_validate__prefs_incorrect_type__exception_raised(self) -> None:
        manifest = ExtensionManifest({**valid_manifest, "preferences": {"id": {"type": "incorrect"}}})
        with pytest.raises(ext_exceptions.ManifestError):
            manifest.validate()

    def test_validate__type_kw_empty_name__exception_raised(self) -> None:
        manifest = ExtensionManifest({**valid_manifest, "preferences": {"id": {"type": "incorrect", "keyword": "kw"}}})
        with pytest.raises(ext_exceptions.ManifestError):
            manifest.validate()

    def test_validate__raises_error_if_empty_default_value_for_keyword(self) -> None:
        manifest = ExtensionManifest(
            {**valid_manifest, "preferences": {"id": {"type": "keyword", "name": "My Keyword"}}}
        )
        with pytest.raises(ext_exceptions.ManifestError):
            manifest.validate()

    def test_validate__doesnt_raise_if_empty_default_value_for_non_keyword(self) -> None:
        manifest = ExtensionManifest({**valid_manifest, "preferences": {"city": {"type": "input", "name": "City"}}})
        manifest.validate()

    def test_validate__trigger_missing_name__exception_raised(self) -> None:
        manifest = ExtensionManifest({**valid_manifest, "triggers": {"t": {}}})
        with pytest.raises(ext_exceptions.ManifestError):
            manifest.validate()

    def test_validate__pref_missing_name__exception_raised(self) -> None:
        manifest = ExtensionManifest({**valid_manifest, "preferences": {"p": {"type": "input"}}})
        with pytest.raises(ext_exceptions.ManifestError):
            manifest.validate()

    def test_validate__min_on_non_number__exception_raised(self) -> None:
        manifest = ExtensionManifest(
            {**valid_manifest, "preferences": {"p": {"type": "input", "name": "Text", "min": 5}}}
        )
        with pytest.raises(ext_exceptions.ManifestError):
            manifest.validate()

    def test_validate__max_on_non_number__exception_raised(self) -> None:
        manifest = ExtensionManifest(
            {**valid_manifest, "preferences": {"p": {"type": "input", "name": "Text", "max": 5}}}
        )
        with pytest.raises(ext_exceptions.ManifestError):
            manifest.validate()

    def test_validate__checkbox_bool_default__no_exception(self) -> None:
        manifest = ExtensionManifest(
            {**valid_manifest, "preferences": {"p": {"type": "checkbox", "name": "Flag", "default_value": True}}}
        )
        manifest.validate()

    def test_validate__checkbox_no_default__no_exception(self) -> None:
        manifest = ExtensionManifest({**valid_manifest, "preferences": {"p": {"type": "checkbox", "name": "Flag"}}})
        manifest.validate()

    def test_validate__checkbox_non_bool_default__exception_raised(self) -> None:
        manifest = ExtensionManifest(
            {**valid_manifest, "preferences": {"p": {"type": "checkbox", "name": "Flag", "default_value": "yes"}}}
        )
        with pytest.raises(ext_exceptions.ManifestError):
            manifest.validate()

    def test_validate__number_valid__no_exception(self) -> None:
        manifest = ExtensionManifest(
            {**valid_manifest, "preferences": {"p": {"type": "number", "name": "Count", "default_value": 5}}}
        )
        manifest.validate()

    def test_validate__number_no_default__exception_raised(self) -> None:
        manifest = ExtensionManifest({**valid_manifest, "preferences": {"p": {"type": "number", "name": "Count"}}})
        with pytest.raises(ext_exceptions.ManifestError):
            manifest.validate()

    def test_validate__number_bool_default__exception_raised(self) -> None:
        manifest = ExtensionManifest(
            {**valid_manifest, "preferences": {"p": {"type": "number", "name": "Count", "default_value": True}}}
        )
        with pytest.raises(ext_exceptions.ManifestError):
            manifest.validate()

    def test_validate__number_min_zero__no_exception(self) -> None:
        manifest = ExtensionManifest(
            {**valid_manifest, "preferences": {"p": {"type": "number", "name": "Count", "default_value": 0, "min": 0}}}
        )
        manifest.validate()

    def test_validate__number_default_below_min__exception_raised(self) -> None:
        manifest = ExtensionManifest(
            {**valid_manifest, "preferences": {"p": {"type": "number", "name": "Count", "default_value": 3, "min": 5}}}
        )
        with pytest.raises(ext_exceptions.ManifestError):
            manifest.validate()

    def test_validate__number_default_above_max__exception_raised(self) -> None:
        manifest = ExtensionManifest(
            {
                **valid_manifest,
                "preferences": {"p": {"type": "number", "name": "Count", "default_value": 15, "max": 10}},
            }
        )
        with pytest.raises(ext_exceptions.ManifestError):
            manifest.validate()

    def test_validate__number_min_above_max__exception_raised(self) -> None:
        manifest = ExtensionManifest(
            {
                **valid_manifest,
                "preferences": {"p": {"type": "number", "name": "Count", "default_value": 10, "min": 8, "max": 3}},
            }
        )
        with pytest.raises(ext_exceptions.ManifestError):
            manifest.validate()

    def test_validate__number_bool_min__exception_raised(self) -> None:
        manifest = ExtensionManifest(
            {
                **valid_manifest,
                "preferences": {"p": {"type": "number", "name": "Count", "default_value": 5, "min": True}},
            }
        )
        with pytest.raises(ext_exceptions.ManifestError):
            manifest.validate()

    def test_validate__number_bool_max__exception_raised(self) -> None:
        manifest = ExtensionManifest(
            {
                **valid_manifest,
                "preferences": {"p": {"type": "number", "name": "Count", "default_value": 5, "max": True}},
            }
        )
        with pytest.raises(ext_exceptions.ManifestError):
            manifest.validate()

    def test_validate__select_with_options__no_exception(self) -> None:
        manifest = ExtensionManifest(
            {
                **valid_manifest,
                "preferences": {"p": {"type": "select", "name": "Choice", "options": [{"value": "a", "text": "A"}]}},
            }
        )
        manifest.validate()

    def test_validate__select_empty_options__exception_raised(self) -> None:
        # Workaround: pyrefly raises implicit-any for `[]` literals, but ruff rejects `list()`.
        # Typed variable avoids both. See https://github.com/facebook/pyrefly/issues/2442
        empty: list[str] = []
        manifest = ExtensionManifest(
            {**valid_manifest, "preferences": {"p": {"type": "select", "name": "Choice", "options": empty}}}
        )
        with pytest.raises(ext_exceptions.ManifestError):
            manifest.validate()

    def test_check_compatibility__manifest_version_0__exception_raised(self) -> None:
        manifest = ExtensionManifest({"name": "Test", "api_version": "0"})
        with pytest.raises(ext_exceptions.CompatibilityError):
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
