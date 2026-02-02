from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from ulauncher import api_version
from ulauncher.modes.extensions import ext_exceptions
from ulauncher.utils.json_conf import JsonConf
from ulauncher.utils.version import satisfies

logger = logging.getLogger()


class ExtensionManifestPreference(JsonConf):
    name = ""
    type = ""
    description = ""
    options: list[dict[str, Any]] = []
    default_value: str | int = ""
    max: int | None = None
    min: int | None = None

    def __setitem__(self, key: str, value: Any) -> None:  # type: ignore[override]
        validate_type = key in ["name", "type", "description", "options"]
        super().__setitem__(key, value, validate_type)


class ExtensionManifestTrigger(JsonConf):
    name = ""
    description = ""
    default_keyword = ""
    icon = ""

    def __setitem__(self, key: str, value: Any) -> None:  # type: ignore[override]
        # Backwards compatibility: rename "keyword" to "default_keyword"
        if key == "keyword":
            key = "default_keyword"
        super().__setitem__(key, value)


class ExtensionManifest(JsonConf):
    api_version = ""
    authors = ""
    name = ""
    icon = ""
    instructions = ""
    input_debounce = 0.05
    triggers: dict[str, ExtensionManifestTrigger] = {}
    preferences: dict[str, ExtensionManifestPreference] = {}

    def __setitem__(self, key: str, value: Any) -> None:  # type: ignore[override]  # noqa: PLR0912
        # Rename "required_api_version" back to "api_version"
        if key == "required_api_version":
            key = "api_version"
        # Rename "developer_name" to "authors"
        elif key == "developer_name":
            key = "authors"
        # Flatten manifest v2 API "options"
        elif key == "options":
            key = "input_debounce"
            value = isinstance(value, dict) and float(value.get("query_debounce", -1))
            if value <= 0:
                return
        # Convert triggers dicts to ExtensionManifestTrigger instances
        elif key == "triggers" and isinstance(value, dict):
            value = {t_id: ExtensionManifestTrigger(trigger) for t_id, trigger in value.items()}
        # Convert preferences dicts to manifest preference instances (or trigger it's an old shortcuts)
        elif key == "preferences":
            if isinstance(value, dict):
                value = {p_id: ExtensionManifestPreference(pref) for p_id, pref in value.items()}
            elif isinstance(value, list):  # APIv2 backwards compatibility
                prefs = {}
                for p in value:
                    if isinstance(p, dict):
                        p_id = p.get("id")
                        if isinstance(p_id, str):
                            pref = ExtensionManifestPreference(p, id=None)
                            if pref.type != "keyword":
                                prefs[p_id] = pref
                            else:
                                self.triggers[p_id] = ExtensionManifestTrigger(
                                    name=pref.name,
                                    description=pref.description,
                                    default_keyword=pref.default_value,
                                    icon=pref.get("icon", ""),
                                )
                value = prefs
        super().__setitem__(key, value)

    def validate(self) -> None:
        """
        Ensure that the manifest is valid (or raise error)
        """
        required_fields = ["api_version", "authors", "name", "icon", "triggers"]
        if missing_fields := [f for f in required_fields if not self.get(f)]:
            err_msg = f'Extension manifest is missing required field(s): "{", ".join(missing_fields)}"'
            raise ext_exceptions.ManifestError(err_msg)

        try:
            for t_id, t in self.triggers.items():
                assert t.name, f'"{t_id}" missing non-optional field "name"'
        except AssertionError as e:
            msg = f"Invalid triggers in Extension manifest: {e}"
            raise ext_exceptions.ManifestError(msg) from None

        try:
            for p_id, p in self.preferences.items():
                valid_types = ["input", "checkbox", "number", "select", "text"]
                default = p.default_value
                assert p.name, f'"{p_id}" missing non-optional field "name"'
                assert p.type, f'"{p_id}" missing non-optional field "type"'
                assert p.type in valid_types, (
                    f'"{p_id}" invalid type "{p.type}" (should be either "{", ".join(valid_types)}")'
                )
                assert p.min is None or p.type == "number", f'"min" specified for "{p_id}", which is not a number type'
                assert p.max is None or p.type == "number", f'"max" specified for "{p_id}", which is not a number type'
                if p.type == "checkbox" and default:
                    assert isinstance(default, bool), f'"{p_id}" "default_value" must be a boolean'
                if p.type == "number":
                    assert isinstance(default, int), f'"{p_id}" default_value must be a non-decimal number'
                    assert not isinstance(default, bool), f'"{p_id}" default_value must be a non-decimal number'
                    assert not p.min or isinstance(p.min, int), (
                        f'"{p_id}" "min" value must be non-decimal number if specified'
                    )
                    assert not p.max or isinstance(p.max, int), (
                        f'"{p_id}" "max" value must be non-decimal number if specified'
                    )
                    assert not p.min or not p.max or p.min < p.max, (
                        f'"{p_id}" "min" value must be lower than "max" if specified'
                    )
                    assert not default or not p.max or default <= p.max, (
                        f'"{p_id}" "default_value" must not be higher than "max"'
                    )
                    assert not default or not p.min or default >= p.min, (
                        f'"{p_id}" "min" value must not be higher than "default_value"'
                    )
                if p.type == "select":
                    assert isinstance(p.options, list), f'"{p_id}" options field must be a list'
                    assert p.options, f'"{p_id}" option cannot be empty for select type'
        except AssertionError as e:
            msg = f"Invalid preferences in Extension manifest: {e}"
            raise ext_exceptions.ManifestError(msg) from None

    def check_compatibility(self, verbose: bool = False) -> None:
        """
        Ensure the extension is compatible with the Ulauncher API (or raise error)
        """
        if not satisfies(api_version, self.api_version):
            if satisfies("2.0", self.api_version):
                # Show a warning for v2 -> v3 instead of aborting. Most v2 extensions run in v3.
                if verbose:
                    logger.warning(
                        "Extension %s has not yet been updated to support API v%s. "
                        "Running in compatibility mode, which may not be fully functional.",
                        self.name,
                        api_version,
                    )
            else:
                msg = f"{self.name} does not support Ulauncher API v{api_version}."
                raise ext_exceptions.CompatibilityError(msg)

    @classmethod
    def load(cls, path: str | Path) -> ExtensionManifest:
        if not str(path).endswith("/manifest.json"):
            path = Path(path, "manifest.json")
        return super().load(path)
