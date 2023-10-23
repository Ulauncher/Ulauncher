from __future__ import annotations

import logging
from typing import Any

from ulauncher.config import API_VERSION, PATHS
from ulauncher.utils.json_conf import JsonConf
from ulauncher.utils.version import satisfies

logger = logging.getLogger()


class ExtensionManifestError(Exception):
    pass


class ExtensionIncompatibleWarning(Exception):
    pass


class Preference(JsonConf):
    name = ""
    type = ""
    description = ""
    options: list[dict] = []
    default_value: str | int = ""
    value: str | int | None = None
    max: int | None = None
    min: int | None = None

    def __setitem__(self, key, value):
        validate_type = key in ["name", "type", "description", "options"]
        super().__setitem__(key, value, validate_type)


class Trigger(JsonConf):
    name = ""
    description = ""
    keyword = ""
    user_keyword = ""
    icon = ""


class ExtensionManifest(JsonConf):
    api_version = ""
    authors = ""
    name = ""
    icon = ""
    instructions = ""
    input_debounce = 0.05
    triggers: dict[str, Trigger] = {}
    preferences: dict[str, Preference] = {}

    def __setitem__(self, key, value):
        # Rename "required_api_version" back to "api_version"
        if key == "required_api_version":
            key = "api_version"
        # Rename "developer_name" to "authors"
        if key == "developer_name":
            key = "authors"
        # Flatten manifest v2 API "options"
        if key == "options":
            key = "input_debounce"
            value = value and float(value.get("query_debounce", -1))
            if value <= 0:
                return
        # Convert triggers dicts to Trigger instances
        if key == "triggers":
            value = {id: Trigger(trigger) for id, trigger in value.items()}
        # Convert preferences dicts to Preference instances (and Triggers if it's old shortcuts)
        if key == "preferences":
            if isinstance(value, dict):
                value = {id: Preference(pref) for id, pref in value.items()}
            elif isinstance(value, list):  # APIv2 backwards compatibility
                prefs = {}
                for p in value:
                    id = p.get("id")
                    pref = Preference(p, id=None)
                    if pref.type != "keyword":
                        prefs[id] = pref
                    else:
                        self.triggers[id] = Trigger(
                            name=pref.name,
                            description=pref.description,
                            keyword=pref.default_value,
                            icon=pref.get("icon", ""),
                        )
                value = prefs
        super().__setitem__(key, value)

    def validate(self):
        """
        Ensure that the manifest is valid (or raise error)
        """
        required_fields = ["api_version", "authors", "name", "icon", "triggers"]
        missing_fields = [f for f in required_fields if not self.get(f)]
        if missing_fields:
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
                assert (
                    p.type in valid_types
                ), f'"{id}" invalid type "{p.type}" (should be either "{", ".join(valid_types)}")'
                assert p.min is None or p.type == "number", f'"min" specified for "{id}", which is not a number type'
                assert p.max is None or p.type == "number", f'"max" specified for "{id}", which is not a number type'
                if p.type == "checkbox" and default:
                    assert isinstance(default, bool), f'"{id}" "default_value" must be a boolean'
                if p.type == "number":
                    assert not default or isinstance(default, int), f'"{id}" default_value must be a non-decimal number'
                    assert not p.min or isinstance(
                        p.min, int
                    ), f'"{id}" "min" value must be non-decimal number if specified'
                    assert not p.max or isinstance(
                        p.min, int
                    ), f'"{id}" "max" value must be non-decimal number if specified'
                    assert (
                        not p.min or not p.max or p.min < p.max
                    ), f'"{id}" "min" value must be lower than "max" if specified'
                    assert (
                        not default or not p.max or default <= p.max
                    ), f'"{id}" "default_value" must not be higher than "max"'
                    assert (
                        not default or not p.min or default >= p.min
                    ), f'"{id}" "min" value must not be higher than "default_value"'
                if p.type == "select":
                    assert isinstance(p.options, list), f'"{id}" options field must be a list'
                    assert p.options, f'"{id}" option cannot be empty for select type'
        except AssertionError as e:
            msg = f"Invalid preferences in Extension manifest: {e}"
            raise ExtensionManifestError(msg) from None

    def check_compatibility(self, verbose=False):
        """
        Ensure the extension is compatible with the Ulauncher API (or raise error)
        """
        if not satisfies(API_VERSION, self.api_version):
            if satisfies("2.0", self.api_version):
                # Show a warning for v2 -> v3 instead of aborting. Most v2 extensions run in v3.
                if verbose:
                    logger.warning(
                        "Extension %s has not yet been updated to support API v%s. "
                        "Running in compatibility mode, which may not be fully functional.",
                        self.name,
                        API_VERSION,
                    )
            else:
                msg = f"{self.name} does not support Ulauncher API v{API_VERSION}."
                raise ExtensionIncompatibleWarning(msg)

    def find_matching_trigger(self, **kwargs) -> str | None:
        """
        Get the first trigger matching the arguments, and returns the id
        Ex find_matching_trigger(user_keyword='asdf', icon=None)
        """
        return next((id for id, t in self.triggers.items() if {**t, **kwargs} == t), None)

    def get_user_preferences(self) -> dict[str, Any]:
        """
        Get the preferences as an id-value dict
        """
        return {id: pref.value for id, pref in self.preferences.items()}

    def save_user_preferences(self, ext_id: str):
        path = f"{PATHS.EXTENSIONS_CONFIG}/{ext_id}.json"
        triggers = {id: ({"keyword": t.user_keyword} if t.keyword else {}) for id, t in self.triggers.items()}
        file = JsonConf.load(path)
        file.update(triggers=triggers, preferences=self.get_user_preferences())
        file.save()

    def apply_user_preferences(self, user_prefs: dict):
        for id, pref in self.preferences.items():
            pref.value = user_prefs.get("preferences", {}).get(id, pref.default_value)

        for id, trigger in self.triggers.items():
            if trigger.keyword:
                trigger.user_keyword = user_prefs.get("triggers", {}).get(id, {}).get("keyword", trigger.keyword)

    @classmethod
    def load_from_extension_id(cls, ext_id: str):
        manifest = super().load(f"{PATHS.EXTENSIONS}/{ext_id}/manifest.json")
        manifest.apply_user_preferences(JsonConf.load(f"{PATHS.EXTENSIONS_CONFIG}/{ext_id}.json"))
        return manifest
