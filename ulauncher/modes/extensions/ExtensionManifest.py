from typing import Any, Optional, List, Union
from ulauncher.config import API_VERSION
from ulauncher.api.shared.errors import UlauncherAPIError, ExtensionError
from ulauncher.utils.json_data import JsonData, json_data_class
from ulauncher.utils.version import satisfies
from ulauncher.utils.mypy_extensions import TypedDict


class ExtensionManifestError(UlauncherAPIError):
    pass


OptionItemExtended = TypedDict('OptionItemExtended', {"value": str, "text": str})
OptionItem = Union[str, OptionItemExtended]
OptionItems = List[OptionItem]
Options = TypedDict("Options", {"query_debounce": float})
ManifestPreference = TypedDict('ManifestPreference', {
    'id': str,
    'type': str,
    'name': str,
    'description': str,
    'default_value': Union[str, int],  # Bool is a subclass of int
    'options': OptionItems,
    'min': Optional[int],
    'max': Optional[int],
    'icon': Optional[str]
})


@json_data_class
class ExtensionManifest(JsonData):
    name = ""
    description = ""
    developer_name = ""
    icon = ""
    required_api_version = ""
    preferences: List[ManifestPreference] = []
    instructions: Optional[str] = None
    options: Optional[Options] = {"query_debounce": 0.0}
    # Filter out the empty values we use as defaults so they're not saved to the JSON
    __json_value_blacklist__: List[Any] = [[], {}, None, ""]  # pylint: disable=dangerous-default-value


    def validate(self):
        try:
            assert self.required_api_version, "required_api_version is not provided"
            assert self.name, "name is not provided"
            assert self.description, "description is not provided"
            assert self.developer_name, "developer_name is not provided"
            assert self.icon, "icon is not provided"
            assert self.preferences, "preferences is not provided"

            for p in self.preferences:
                default = p.get('default_value')
                type = p.get('type')
                min = p.get('min')
                max = p.get('max')
                assert p.get('id'), 'Preferences error. Id cannot be empty'
                assert type, 'Preferences error. Type cannot be empty'
                assert type in ["keyword", "checkbox", "number", "input", "select", "text"], \
                    'Preferences error. Type can be "keyword", "input", "number", "checkbox", "select" or "text"'
                assert p.get('name'), 'Preferences error. Name cannot be empty'
                if p['type'] == 'keyword':
                    assert default, 'Preferences error. Keyword default value cannot be empty'
                    assert isinstance(default, str), \
                        'Preferences error. Keyword default value must be a string'
                assert min is None or type == 'number', \
                    'Preferences error. Only number type supports min'
                assert max is None or type == 'number', \
                    'Preferences error. Only number type supports max'
                if type == 'checkbox' and default:
                    assert isinstance(default, bool), \
                        'Preferences error. Checkbox default value must be a boolean'
                if type == 'number':
                    assert not default or isinstance(default, int), \
                        'Preferences error. Number default value must be a non-decimal number'
                    assert not min or isinstance(min, int), \
                        'Preferences error. Number "min" value must be unspecified or a non-decimal number'
                    assert not max or isinstance(min, int), \
                        'Preferences error. Number "max" value must be unspecified or a non-decimal number'
                    assert not min or not max or min < max, \
                        'Preferences error. Number "min" value must be lower than "max" if specified'
                    assert not default or not max or default <= max, \
                        'Preferences error. Number default value must not be higher than "max"'
                    assert not default or not min or default >= min, \
                        'Preferences error. Number "min" value must not be higher than default value'
                if type == 'select':
                    assert isinstance(p.get('options'), list), 'Preferences error. Options must be a list'
                    assert p.get('options'), 'Preferences error. Option list cannot be empty'
        except AssertionError as e:
            raise ExtensionManifestError(str(e), ExtensionError.InvalidManifest) from e
        except KeyError as e:
            raise ExtensionManifestError(f'{e} is not provided', ExtensionError.InvalidManifest) from e

    def check_compatibility(self):
        if not satisfies(API_VERSION, self.required_api_version):
            err_msg = (
                f'Extension "{self.name}" requires API version {self.required_api_version}, '
                f'but the current API version is: {API_VERSION})'
            )
            raise ExtensionManifestError(err_msg, ExtensionError.Incompatible)
