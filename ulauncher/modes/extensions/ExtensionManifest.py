from typing import Any, cast, Optional, List, Union

from ulauncher.config import API_VERSION, EXTENSIONS_DIR, EXT_PREFERENCES_DIR
from ulauncher.api.shared.errors import UlauncherAPIError, ExtensionError
from ulauncher.utils.json_data import JsonData, json_data_class
from ulauncher.utils.version import satisfies
from ulauncher.utils.mypy_extensions import TypedDict

OptionItem = TypedDict('OptionItem', {"value": str, "text": str})
ValueType = Union[str, int]  # Bool is a subclass of int


class ExtensionManifestError(UlauncherAPIError):
    pass


@json_data_class
class Preference(JsonData):
    id = ""
    name = ""
    type = ""
    description = ""
    default_value: ValueType = ""
    value: Optional[ValueType] = None
    options: List[OptionItem] = []
    max: Optional[int] = None
    min: Optional[int] = None
    icon: Optional[str] = None


@json_data_class
class ExtensionManifest(JsonData):
    name = ""
    description = ""
    developer_name = ""
    icon = ""
    required_api_version = ""
    preferences: List[Preference] = []
    instructions: Optional[str] = None
    query_debounce: Optional[float] = None
    # Filter out the empty values we use as defaults so they're not saved to the JSON
    __json_value_blacklist__: List[Any] = [[], {}, None, ""]  # pylint: disable=dangerous-default-value

    def __setitem__(self, key, value):
        # Flatten manifest v2 API "options"
        if key == "options":
            key = "query_debounce"
            value = value and value.get("query_debounce")
            if value is None:
                return
        # Coerce preferences to Preference
        if key == "preferences":
            value = [Preference(pref) for pref in value]
        super().__setitem__(key, value)

    def validate(self):
        """
        Ensure that the manifest is valid (or raise error)
        """
        try:
            assert self.required_api_version, "required_api_version is not provided"
            assert self.name, "name is not provided"
            assert self.description, "description is not provided"
            assert self.developer_name, "developer_name is not provided"
            assert self.icon, "icon is not provided"
            assert self.preferences, "preferences is not provided"

            for p in self.preferences:
                default = p.default_value
                assert p.id, 'Preferences error. Id cannot be empty'
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
        except KeyError as e:
            raise ExtensionManifestError(f'{e} is not provided', ExtensionError.InvalidManifest) from e

    def check_compatibility(self):
        """
        Ensure the extension is compatible with the Ulauncher API (or raise error)
        """
        if not satisfies(API_VERSION, self.required_api_version):
            err_msg = (
                f'Extension "{self.name}" requires API version {self.required_api_version}, '
                f'but the current API version is: {API_VERSION})'
            )
            raise ExtensionManifestError(err_msg, ExtensionError.Incompatible)

    def get_preference(self, **kwargs) -> Optional[Preference]:
        """
        Get the first preference matching the arguments
        Ex manifest.get_preference(type="number", name="my_number")
        """
        for pref in self.preferences:
            if {**pref, **kwargs} == pref:
                return pref
        return None

    def get_preferences_dict(self):
        """
        Get the preferences as an id-value dict
        """
        return {p.id: p.value for p in self.preferences}

    def save_user_preferences(self, ext_id: str):
        path = f"{EXT_PREFERENCES_DIR}/{ext_id}.json"
        JsonData.new_from_file(path).save(self.get_preferences_dict())

    @classmethod
    def load_from_extension_id(cls, ext_id: str):
        manifest = cls.new_from_file(f"{EXTENSIONS_DIR}/{ext_id}/manifest.json")
        user_prefs = cast(JsonData, JsonData.new_from_file(f"{EXT_PREFERENCES_DIR}/{ext_id}.json"))
        for pref in manifest.preferences:
            if user_prefs.get(pref.id):
                pref.value = user_prefs.get(pref.id)

        return manifest
