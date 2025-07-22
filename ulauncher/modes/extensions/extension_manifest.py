from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from ulauncher import api_version, paths
from ulauncher.utils.json_conf import JsonConf
from ulauncher.utils.version import satisfies

logger = logging.getLogger()


class ExtensionManifestError(Exception):
    pass


class ExtensionIncompatibleRecoverableError(Exception):
    pass


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
    keyword = ""
    icon = ""


class UserPreference(ExtensionManifestPreference):
    value: str | int | None = None


class UserTrigger(ExtensionManifestTrigger):
    user_keyword = ""


class ExtensionManifest(JsonConf):
    api_version = ""
    authors = ""
    name = ""
    icon = ""
    instructions = ""
    input_debounce = 0.05
    triggers: dict[str, ExtensionManifestTrigger] = {}
    preferences: dict[str, ExtensionManifestPreference] = {}

    def __setitem__(self, key: str, value: Any) -> None:  # type: ignore[override]
        # Rename "required_api_version" back to "api_version"
        if key == "required_api_version":
            key = "api_version"
        # Rename "developer_name" to "authors"
        elif key == "developer_name":
            key = "authors"
        # Flatten manifest v2 API "options"
        elif key == "options":
            key = "input_debounce"
            value = value and float(value.get("query_debounce", -1))
            if value <= 0:
                return
        # Convert triggers dicts to ExtensionManifestTrigger instances
        elif key == "triggers":
            value = {id: ExtensionManifestTrigger(trigger) for id, trigger in value.items()}
        # Convert preferences dicts to manifest preference instances (or trigger it's an old shortcuts)
        elif key == "preferences":
            if isinstance(value, dict):
                value = {id: ExtensionManifestPreference(pref) for id, pref in value.items()}
            elif isinstance(value, list):  # APIv2 backwards compatibility
                prefs = {}
                for p in value:
                    id = p.get("id")
                    pref = ExtensionManifestPreference(p, id=None)
                    if pref.type != "keyword":
                        prefs[id] = pref
                    else:
                        self.triggers[id] = ExtensionManifestTrigger(
                            name=pref.name,
                            description=pref.description,
                            keyword=pref.default_value,
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
            raise ExtensionManifestError(err_msg)

        try:
            for id, t in self.triggers.items():
                assert t.name, f'"{id}" missing non-optional field "name"'
        except AssertionError as e:
            msg = f"Invalid triggers in Extension manifest: {e}"
            raise ExtensionManifestError(msg) from None

        try:
            for id, p in self.preferences.items():
                valid_types = ["input", "checkbox", "number", "select", "text"]
                default = p.default_value
                assert p.name, f'"{id}" missing non-optional field "name"'
                assert p.type, f'"{id}" missing non-optional field "type"'
                assert p.type in valid_types, (
                    f'"{id}" invalid type "{p.type}" (should be either "{", ".join(valid_types)}")'
                )
                assert p.min is None or p.type == "number", f'"min" specified for "{id}", which is not a number type'
                assert p.max is None or p.type == "number", f'"max" specified for "{id}", which is not a number type'
                if p.type == "checkbox" and default:
                    assert isinstance(default, bool), f'"{id}" "default_value" must be a boolean'
                if p.type == "number":
                    assert isinstance(default, int), f'"{id}" default_value must be a non-decimal number'
                    assert not isinstance(default, bool), f'"{id}" default_value must be a non-decimal number'
                    assert not p.min or isinstance(p.min, int), (
                        f'"{id}" "min" value must be non-decimal number if specified'
                    )
                    assert not p.max or isinstance(p.min, int), (
                        f'"{id}" "max" value must be non-decimal number if specified'
                    )
                    assert not p.min or not p.max or p.min < p.max, (
                        f'"{id}" "min" value must be lower than "max" if specified'
                    )
                    assert not default or not p.max or default <= p.max, (
                        f'"{id}" "default_value" must not be higher than "max"'
                    )
                    assert not default or not p.min or default >= p.min, (
                        f'"{id}" "min" value must not be higher than "default_value"'
                    )
                if p.type == "select":
                    assert isinstance(p.options, list), f'"{id}" options field must be a list'
                    assert p.options, f'"{id}" option cannot be empty for select type'
        except AssertionError as e:
            msg = f"Invalid preferences in Extension manifest: {e}"
            raise ExtensionManifestError(msg) from None

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
                raise ExtensionIncompatibleRecoverableError(msg)

    def _get_raw_preferences(self, ext_id: str) -> JsonConf:
        return JsonConf.load(f"{paths.EXTENSIONS_CONFIG}/{ext_id}.json")

    def get_user_preferences(self, ext_id: str) -> dict[str, UserPreference]:
        user_prefs_json = self._get_raw_preferences(ext_id)
        user_prefs = {}
        for id, pref in self.preferences.items():
            # copy to avoid mutating
            user_pref = UserPreference(**pref)
            user_pref.value = user_prefs_json.get("preferences", {}).get(id, pref.default_value)
            user_prefs[id] = user_pref
        return user_prefs

    def get_user_triggers(self, ext_id: str) -> dict[str, UserTrigger]:
        user_prefs_json = self._get_raw_preferences(ext_id)
        user_triggers = {}
        for id, trigger in self.triggers.items():
            combined_trigger = UserTrigger(trigger)
            if trigger.keyword:
                user_keyword = user_prefs_json.get("triggers", {}).get(id, {}).get("keyword", trigger.keyword)
                combined_trigger.user_keyword = user_keyword
            user_triggers[id] = combined_trigger

        return user_triggers

    def save_user_preferences(self, ext_id: str, data: Any) -> None:
        user_prefs_json = self._get_raw_preferences(ext_id)
        user_prefs_json.save(data)

    @classmethod
    def load(cls, path: str | Path) -> ExtensionManifest:
        if not str(path).endswith("/manifest.json"):
            path = Path(path, "manifest.json")
        return super().load(path)
