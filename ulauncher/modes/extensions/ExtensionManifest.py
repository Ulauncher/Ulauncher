import logging
from typing import Any, Dict, Optional, List, Union

from ulauncher.config import API_VERSION, PATHS
from ulauncher.utils.json_data import JsonData, json_data_class
from ulauncher.utils.version import satisfies

logger = logging.getLogger()
ValueType = Union[str, int]  # Bool is a subclass of int


class ExtensionManifestError(Exception):
    pass


class ExtensionIncompatibleWarning(Exception):
    pass


@json_data_class
class Preference(JsonData):
    name = ""
    type = ""
    description = ""
    default_value: ValueType = ""
    value: Optional[ValueType] = None
    options: List[dict] = []
    max: Optional[int] = None
    min: Optional[int] = None
    icon: Optional[str] = None


@json_data_class
class ExtensionManifest(JsonData):
    api_version = ""
    name = ""
    developer_name = ""
    icon = ""
    preferences: Dict[str, Preference] = {}
    instructions: Optional[str] = None
    query_debounce: Optional[float] = None
    # Filter out the empty values we use as defaults so they're not saved to the JSON
    __json_value_blacklist__: List[Any] = [[], {}, None, ""]  # pylint: disable=dangerous-default-value

    def __setitem__(self, key, value):
        # Rename "required_api_version" back to "api_version"
        if key == "required_api_version":
            key = "api_version"
        # Flatten manifest v2 API "options"
        if key == "options":
            key = "query_debounce"
            value = value and value.get("query_debounce")
            if value is None:
                return
        # Coerce preferences to Preference
        if key == "preferences":
            if isinstance(value, list):
                value = {pref.get("id"): Preference(pref, id=None) for pref in value}
            else:
                value = {id: Preference(pref) for id, pref in value.items()}
        super().__setitem__(key, value)

    def validate(self):
        """
        Ensure that the manifest is valid (or raise error)
        """
        required_fields = [key for key, val in self.__default_props__.items() if val is not None]
        missing_fields = [f for f in required_fields if not self.get(f)]
        if missing_fields:
            err_msg = f'Extension manifest is missing required field(s): "{", ".join(missing_fields)}"'
            raise ExtensionManifestError(err_msg)
        try:
            for id, p in self.preferences.items():
                valid_types = ["keyword", "checkbox", "number", "input", "select", "text"]
                default = p.default_value
                assert p.name, f'"{id}" missing non-optional field "name"'
                assert p.type, f'"{id}" missing non-optional field "type"'
                assert p.type in valid_types, \
                    f'"{id}" invalid type "{p.type}" (should be either "{", ".join(valid_types)}")'
                if p.type == 'keyword':
                    assert default, f'"{id}" keyword default value must be a non-empty string'
                assert p.min is None or p.type == 'number', \
                    f'"min" specified for "{id}", which is not a number type'
                assert p.max is None or p.type == 'number', \
                    f'"max" specified for "{id}", which is not a number type'
                if p.type == 'checkbox' and default:
                    assert isinstance(default, bool), \
                        f'"{id}" "default_value" must be a boolean'
                if p.type == 'number':
                    assert not default or isinstance(default, int), \
                        f'"{id}" default_value must be a non-decimal number'
                    assert not p.min or isinstance(p.min, int), \
                        f'"{id}" "min" value must be non-decimal number if specified'
                    assert not p.max or isinstance(p.min, int), \
                        f'"{id}" "max" value must be non-decimal number if specified'
                    assert not p.min or not p.max or p.min < p.max, \
                        f'"{id}" "min" value must be lower than "max" if specified'
                    assert not default or not p.max or default <= p.max, \
                        f'"{id}" "default_value" must not be higher than "max"'
                    assert not default or not p.min or default >= p.min, \
                        f'"{id}" "min" value must not be higher than "default_value"'
                if p.type == 'select':
                    assert isinstance(p.options, list), f'"{id}" options field must be a list'
                    assert p.options, f'"{id}" option cannot be empty for select type'
        except AssertionError as e:
            raise ExtensionManifestError(f"Invalid preferences in Extension manifest: {str(e)}") from None

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
                        "It might fail to start or not be fully functional.",
                        self.name,
                        API_VERSION
                    )
            else:
                raise ExtensionIncompatibleWarning(f'{self.name} does not support Ulauncher API v{API_VERSION}.')

    def get_user_preferences(self) -> Dict[str, Any]:
        """
        Get the preferences as an id-value dict
        """
        return {id: pref.value for id, pref in self.preferences.items()}

    def save_user_preferences(self, ext_id: str):
        path = f"{PATHS.EXTENSIONS_CONFIG}/{ext_id}.json"
        JsonData.new_from_file(path).save(self.get_user_preferences())

    @classmethod
    def load_from_extension_id(cls, ext_id: str):
        manifest = cls.new_from_file(f"{PATHS.EXTENSIONS}/{ext_id}/manifest.json")
        user_prefs = JsonData.new_from_file(f"{PATHS.EXTENSIONS_CONFIG}/{ext_id}.json")
        for id, pref in manifest.preferences.items():
            user_value = user_prefs.get(id)
            pref.value = pref.default_value if user_value is None else user_value

        return manifest
