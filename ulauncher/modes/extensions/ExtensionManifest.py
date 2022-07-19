import logging
from typing import Any, Dict, Optional, List, Union

from ulauncher.config import API_VERSION, PATHS
from ulauncher.api.shared.errors import UlauncherAPIError, ExtensionError
from ulauncher.utils.json_data import JsonData, json_data_class
from ulauncher.utils.version import satisfies

logger = logging.getLogger()
ValueType = Union[str, int]  # Bool is a subclass of int
EXT_PREFERENCES_DIR = f"{PATHS.CONFIG}/ext_preferences"


class ExtensionManifestError(UlauncherAPIError):
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
        try:
            assert self.api_version, "api_version is not provided"
            assert self.name, "name is not provided"
            assert self.developer_name, "developer_name is not provided"
            assert self.icon, "icon is not provided"
            assert self.preferences, "preferences is not provided"

            for p in self.preferences.values():
                default = p.default_value
                assert p.type, 'Preferences error. Type cannot be empty'
                assert p.type in ["keyword", "checkbox", "number", "input", "select", "text"], \
                    'Preferences error. Type can be "keyword", "input", "number", "checkbox", "select" or "text"'
                assert p.name, 'Preferences error. Name cannot be empty'
                if p.type == 'keyword':
                    assert default, 'Preferences error. Keyword default value cannot be empty'
                    assert isinstance(default, str), \
                        'Preferences error. Keyword default value must be a string'
                assert p.min is None or p.type == 'number', \
                    'Preferences error. Only number type supports min'
                assert p.max is None or p.type == 'number', \
                    'Preferences error. Only number type supports max'
                if p.type == 'checkbox' and default:
                    assert isinstance(default, bool), \
                        'Preferences error. Checkbox default value must be a boolean'
                if p.type == 'number':
                    assert not default or isinstance(default, int), \
                        'Preferences error. Number default value must be a non-decimal number'
                    assert not p.min or isinstance(p.min, int), \
                        'Preferences error. Number "min" value must be unspecified or a non-decimal number'
                    assert not p.max or isinstance(p.min, int), \
                        'Preferences error. Number "max" value must be unspecified or a non-decimal number'
                    assert not p.min or not p.max or p.min < p.max, \
                        'Preferences error. Number "min" value must be lower than "max" if specified'
                    assert not default or not p.max or default <= p.max, \
                        'Preferences error. Number default value must not be higher than "max"'
                    assert not default or not p.min or default >= p.min, \
                        'Preferences error. Number "min" value must not be higher than default value'
                if p.type == 'select':
                    assert isinstance(p.options, list), 'Preferences error. Options must be a list'
                    assert p.options, 'Preferences error. Option list cannot be empty'
        except AssertionError as e:
            raise ExtensionManifestError(str(e), ExtensionError.InvalidManifest) from e

    def check_compatibility(self, verbose=False):
        """
        Ensure the extension is compatible with the Ulauncher API (or raise error)
        """
        if not satisfies(API_VERSION, self.api_version):
            err_msg = (
                f'Extension "{self.name}" supports API version(s) {self.api_version}, '
                f'but the Ulauncher version you are running is using extension API v:{API_VERSION}).'
            )
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
                raise ExtensionManifestError(err_msg, ExtensionError.Incompatible)

    def get_user_preferences(self) -> Dict[str, Any]:
        """
        Get the preferences as an id-value dict
        """
        return {id: pref.value for id, pref in self.preferences.items()}

    def save_user_preferences(self, ext_id: str):
        path = f"{EXT_PREFERENCES_DIR}/{ext_id}.json"
        JsonData.new_from_file(path).save(self.get_user_preferences())

    @classmethod
    def load_from_extension_id(cls, ext_id: str):
        manifest = cls.new_from_file(f"{PATHS.EXTENSIONS}/{ext_id}/manifest.json")
        user_prefs = JsonData.new_from_file(f"{EXT_PREFERENCES_DIR}/{ext_id}.json")
        for id, pref in manifest.preferences.items():
            user_value = user_prefs.get(id)
            pref.value = pref.default_value if user_value is None else user_value

        return manifest
