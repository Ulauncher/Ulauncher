from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from ulauncher import api_version
from ulauncher.data import JsonConf
from ulauncher.modes.extensions import ext_exceptions
from ulauncher.utils.version import satisfies

logger = logging.getLogger()


class ExtensionManifestPreference(JsonConf):
    name = ""
    type = ""
    description = ""
    options: list[dict[str, Any]] = []
    default_value: str | int | bool = ""
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

        for t_id, t in self.triggers.items():
            if not t.name:
                msg = f'Invalid triggers in Extension manifest: "{t_id}" missing non-optional field "name"'
                raise ext_exceptions.ManifestError(msg)

        for p_id, p in self.preferences.items():
            err_msg = self._validate_pref(p)
            if err_msg:
                raise ext_exceptions.ManifestError(f'Invalid preferences in Extension manifest: "{p_id}": ' + err_msg)

    def _validate_pref(self, pref: ExtensionManifestPreference) -> str | None:  # noqa: PLR0911, PLR0912
        valid_types = ["input", "checkbox", "number", "select", "text"]
        if not pref.name:
            return 'missing non-optional field "name"'
        if not pref.type:
            return 'missing non-optional field "type"'
        if pref.type not in valid_types:
            return f'invalid type "{pref.type}" (should be either "{", ".join(valid_types)}")'
        if pref.min is not None and pref.type != "number":
            return '"min" must be a number type'
        if pref.max is not None and pref.type != "number":
            return '"max" must be a number type'
        if (
            pref.type == "checkbox"
            and pref.default_value != ExtensionManifestPreference.default_value
            and not isinstance(pref.default_value, bool)
        ):
            return '"default_value" must be a boolean'
        if pref.type == "number":
            if type(pref.default_value) is not int:
                return "default_value must be a non-decimal number"
            if pref.min is not None:
                if type(pref.min) is not int:
                    return '"min" value must be a non-decimal number'
                if pref.default_value < pref.min:
                    return '"min" value must not be higher than "default_value"'
            if pref.max is not None:
                if type(pref.max) is not int:
                    return '"max" value must be a non-decimal number'
                if pref.default_value > pref.max:
                    return '"default_value" must not be higher than "max"'
            if type(pref.min) is int and type(pref.max) is int and pref.min >= pref.max:
                return '"min" value must be lower than "max"'
        if pref.type == "select":
            if not isinstance(pref.options, list):
                return "options field must be a list"
            if not pref.options:
                return "option cannot be empty for select type"
        return None

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
