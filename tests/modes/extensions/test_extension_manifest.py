from __future__ import annotations

import json
import os
from pathlib import Path
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


def manifest_with(**overrides: Any) -> ExtensionManifest:
    merged: dict[str, Any] = {**valid_manifest, **overrides}
    return ExtensionManifest(**merged)


class TestExtensionManifest:
    def test_open__manifest_file__is_read(self) -> None:
        ext_path = os.path.dirname(os.path.abspath(__file__))
        manifest = ExtensionManifest.load(f"{ext_path}/test_extension/manifest.json")
        assert manifest.name == "Test Extension"

    def test_validate__name_empty__exception_raised(self) -> None:
        manifest = ExtensionManifest(api_version="1")
        with pytest.raises(ext_exceptions.ManifestError):
            manifest.validate()

    def test_validate__valid_manifest__no_exceptions_raised(self) -> None:
        manifest = manifest_with()
        manifest.validate()

    def test_validate__prefs_incorrect_type__exception_raised(self) -> None:
        manifest = manifest_with(preferences={"id": {"type": "incorrect"}})
        with pytest.raises(ext_exceptions.ManifestError):
            manifest.validate()

    def test_validate__type_kw_empty_name__exception_raised(self) -> None:
        manifest = manifest_with(preferences={"id": {"type": "incorrect", "keyword": "kw"}})
        with pytest.raises(ext_exceptions.ManifestError):
            manifest.validate()

    def test_validate__raises_error_if_empty_default_value_for_keyword(self) -> None:
        manifest = manifest_with(preferences={"id": {"type": "keyword", "name": "My Keyword"}})
        with pytest.raises(ext_exceptions.ManifestError):
            manifest.validate()

    def test_validate__doesnt_raise_if_empty_default_value_for_non_keyword(self) -> None:
        manifest = manifest_with(preferences={"city": {"type": "input", "name": "City"}})
        manifest.validate()

    def test_validate__trigger_missing_name__exception_raised(self) -> None:
        manifest = manifest_with(triggers={"t": {}})
        with pytest.raises(ext_exceptions.ManifestError):
            manifest.validate()

    def test_validate__pref_missing_name__exception_raised(self) -> None:
        manifest = manifest_with(preferences={"p": {"type": "input"}})
        with pytest.raises(ext_exceptions.ManifestError):
            manifest.validate()

    def test_validate__min_on_non_number__exception_raised(self) -> None:
        manifest = manifest_with(preferences={"p": {"type": "input", "name": "Text", "min": 5}})
        with pytest.raises(ext_exceptions.ManifestError):
            manifest.validate()

    def test_validate__max_on_non_number__exception_raised(self) -> None:
        manifest = manifest_with(preferences={"p": {"type": "input", "name": "Text", "max": 5}})
        with pytest.raises(ext_exceptions.ManifestError):
            manifest.validate()

    def test_validate__checkbox_bool_default__no_exception(self) -> None:
        manifest = manifest_with(preferences={"p": {"type": "checkbox", "name": "Flag", "default_value": True}})
        manifest.validate()

    def test_validate__checkbox_no_default__no_exception(self) -> None:
        manifest = manifest_with(preferences={"p": {"type": "checkbox", "name": "Flag"}})
        manifest.validate()

    def test_validate__checkbox_non_bool_default__exception_raised(self) -> None:
        manifest = manifest_with(preferences={"p": {"type": "checkbox", "name": "Flag", "default_value": "yes"}})
        with pytest.raises(ext_exceptions.ManifestError):
            manifest.validate()

    def test_validate__number_valid__no_exception(self) -> None:
        manifest = manifest_with(preferences={"p": {"type": "number", "name": "Count", "default_value": 5}})
        manifest.validate()

    def test_validate__number_no_default__exception_raised(self) -> None:
        manifest = manifest_with(preferences={"p": {"type": "number", "name": "Count"}})
        with pytest.raises(ext_exceptions.ManifestError):
            manifest.validate()

    def test_validate__number_bool_default__exception_raised(self) -> None:
        manifest = manifest_with(preferences={"p": {"type": "number", "name": "Count", "default_value": True}})
        with pytest.raises(ext_exceptions.ManifestError):
            manifest.validate()

    def test_validate__number_min_zero__no_exception(self) -> None:
        manifest = manifest_with(preferences={"p": {"type": "number", "name": "Count", "default_value": 0, "min": 0}})
        manifest.validate()

    def test_validate__number_default_below_min__exception_raised(self) -> None:
        manifest = manifest_with(preferences={"p": {"type": "number", "name": "Count", "default_value": 3, "min": 5}})
        with pytest.raises(ext_exceptions.ManifestError):
            manifest.validate()

    def test_validate__number_default_above_max__exception_raised(self) -> None:
        manifest = manifest_with(preferences={"p": {"type": "number", "name": "Count", "default_value": 15, "max": 10}})
        with pytest.raises(ext_exceptions.ManifestError):
            manifest.validate()

    def test_validate__number_min_above_max__exception_raised(self) -> None:
        manifest = manifest_with(
            preferences={"p": {"type": "number", "name": "Count", "default_value": 10, "min": 8, "max": 3}}
        )
        with pytest.raises(ext_exceptions.ManifestError):
            manifest.validate()

    def test_validate__number_bool_min__exception_raised(self) -> None:
        manifest = manifest_with(
            preferences={"p": {"type": "number", "name": "Count", "default_value": 5, "min": True}}
        )
        with pytest.raises(ext_exceptions.ManifestError):
            manifest.validate()

    def test_validate__number_bool_max__exception_raised(self) -> None:
        manifest = manifest_with(
            preferences={"p": {"type": "number", "name": "Count", "default_value": 5, "max": True}}
        )
        with pytest.raises(ext_exceptions.ManifestError):
            manifest.validate()

    def test_validate__select_with_options__no_exception(self) -> None:
        manifest = manifest_with(
            preferences={"p": {"type": "select", "name": "Choice", "options": [{"value": "a", "text": "A"}]}}
        )
        manifest.validate()

    def test_validate__select_empty_options__exception_raised(self) -> None:
        # Workaround: pyrefly raises implicit-any for `[]` literals, but ruff rejects `list()`.
        # Typed variable avoids both. See https://github.com/facebook/pyrefly/issues/2442
        empty: list[str] = []
        manifest = manifest_with(preferences={"p": {"type": "select", "name": "Choice", "options": empty}})
        with pytest.raises(ext_exceptions.ManifestError):
            manifest.validate()

    def test_check_compatibility__manifest_version_0__exception_raised(self) -> None:
        manifest = ExtensionManifest(name="Test", api_version="0")
        with pytest.raises(ext_exceptions.CompatibilityError):
            manifest.check_compatibility()

    def test_check_compatibility__api_version__no_exceptions(self) -> None:
        manifest = ExtensionManifest(name="Test", api_version="3")
        manifest.check_compatibility()

    def test_defaults_not_included_in_stringify(self) -> None:
        # Ensure defaults don't leak
        assert json_stringify(ExtensionManifest()) == '{"input_debounce": 0.05}'
        # __setitem__ converts the raw dict into ExtensionManifestPreference instances.
        raw: dict[str, Any] = {"preferences": {"ns": {"k": "v"}}}
        manifest = ExtensionManifest(**raw)
        assert json_stringify(manifest) == '{"input_debounce": 0.05, "preferences": {"ns": {"k": "v"}}}'

    def test_manifest_backwards_compatibility(self) -> None:
        # Legacy key names, renamed by ExtensionManifest.__setitem__ rather than declared as fields.
        legacy: dict[str, Any] = {
            "required_api_version": "3",
            "developer_name": "John",
            "manifest_version": "1",
            "description": "asdf",
            "options": {"query_debounce": 0.555},
            "preferences": [{"id": "asdf", "name": "ghjk"}],
        }
        em = ExtensionManifest(**legacy)
        assert em.get("options") is None
        assert em.get("required_api_version") is None
        assert em.get("developer_name") is None
        assert em.api_version == "3"
        assert em.authors == "John"
        assert em.input_debounce == 0.555
        asdf = em.preferences.get("asdf")
        assert asdf
        assert asdf.name == "ghjk"


class TestExtensionManifestLoad:
    def write(self, dir_path: Path, **overrides: Any) -> None:
        (dir_path / "manifest.json").write_text(json.dumps({**valid_manifest, **overrides}))

    @pytest.mark.parametrize(
        "overrides",
        [
            pytest.param({"validate": 1}, id="key shadowing a class member"),
            pytest.param({"options": {"query_debounce": "abc"}}, id="non-numeric query_debounce"),
            pytest.param({"triggers": {"t": [1, 2]}}, id="trigger that is not a mapping"),
            pytest.param({"preferences": {"p": 5}}, id="preference that is not a mapping"),
            pytest.param({"triggers": "abc"}, id="triggers that is not an object"),
            pytest.param({"preferences": "abc"}, id="preferences that is neither an object nor a list"),
        ],
    )
    def test_load__unparsable_manifest__raises_manifest_error(self, tmp_path: Path, overrides: dict[str, Any]) -> None:
        self.write(tmp_path, **overrides)
        with pytest.raises(ext_exceptions.ManifestError):
            ExtensionManifest.load(str(tmp_path))

    def test_load__unparsable_manifest__keeps_the_last_parsed_one(self, tmp_path: Path) -> None:
        self.write(tmp_path)
        assert ExtensionManifest.load(str(tmp_path)).name == "Timer"

        self.write(tmp_path, name="Evil", validate=1)
        with pytest.raises(ext_exceptions.ManifestError):
            ExtensionManifest.load(str(tmp_path), force=True)

        # the instance is shared by everything that loaded this path, so a rejected reload
        # must not leave it half-populated
        assert ExtensionManifest.load(str(tmp_path)).name == "Timer"

    def test_load__legacy_keys__are_converted(self, tmp_path: Path) -> None:
        self.write(tmp_path, options={"query_debounce": 0.5})
        manifest = ExtensionManifest.load(str(tmp_path))
        assert manifest.get("options") is None
        assert manifest.input_debounce == 0.5
        assert manifest.triggers["keyword"].default_keyword == "ti"
