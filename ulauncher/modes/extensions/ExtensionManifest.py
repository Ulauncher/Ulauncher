import os
from json import load
from typing import Optional, List, Union
from ulauncher.config import API_VERSION, EXTENSIONS_DIR
from ulauncher.api.shared.errors import UlauncherAPIError, ExtensionError
from ulauncher.utils.version import satisfies
from ulauncher.utils.mypy_extensions import TypedDict
from ulauncher.utils.icon import get_icon_path


class ExtensionManifestError(UlauncherAPIError):
    pass


OptionItemExtended = TypedDict('OptionItemExtended', {
    'value': str,
    'text': str
})
OptionItem = Union[str, OptionItemExtended]
OptionItems = List[OptionItem]
Options = TypedDict('Options', {
    'query_debounce': float
})
ManifestPreferenceItem = TypedDict(
    'ManifestPreferenceItem', {
        'id': str,
        'type': str,
        'name': str,
        'description': str,
        'default_value': Union[str, int],  # Bool is a subclass of int
        'options': OptionItems,
        'icon': Optional[str]
    })
ManifestJson = TypedDict('ManifestJson', {
    'required_api_version': str,
    'name': str,
    'description': str,
    'developer_name': str,
    'icon': str,
    'instructions': Optional[str],
    'min': Optional[int],
    'max': Optional[int],
    'options': Optional[Options],
    'preferences': List[ManifestPreferenceItem]
})


class ExtensionManifest:
    """
    Reads `manifest.json`
    """
    manifest = None  # type: ManifestJson

    @classmethod
    def open(cls, extension_id, extensions_dir=EXTENSIONS_DIR):
        return cls(extension_id, read_manifest(extension_id, extensions_dir), extensions_dir)

    def __init__(self, extension_id: str, manifest: ManifestJson, extensions_dir: str = EXTENSIONS_DIR):
        self.extensions_dir = extensions_dir
        self.extension_id = extension_id
        self.manifest = manifest

    def get_name(self) -> str:
        return self.manifest['name']

    def get_description(self) -> str:
        return self.manifest['description']

    def get_icon(self) -> str:
        return self.manifest['icon']

    def get_icon_path(self, path=None) -> str:
        icon = path or self.get_icon()
        base_path = os.path.join(self.extensions_dir, self.extension_id)
        return get_icon_path(icon, base_path=base_path)

    def get_required_api_version(self) -> str:
        return self.manifest['required_api_version']

    def get_developer_name(self) -> str:
        return self.manifest['developer_name']

    def get_preferences(self) -> List[ManifestPreferenceItem]:
        return self.manifest.get('preferences', [])

    def get_instructions(self) -> Optional[str]:
        return self.manifest.get('instructions')

    def get_option(self, name, default=None):
        return self.manifest.get('options', {}).get(name, default)

    def validate(self):
        try:
            assert self.get_required_api_version(), "required_api_version is not provided"
            assert self.get_name(), 'name is not provided'
            assert self.get_description(), 'description is not provided'
            assert self.get_developer_name(), 'developer_name is not provided'
            assert self.get_icon(), 'icon is not provided'

            for p in self.get_preferences():
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
        if not satisfies(API_VERSION, self.get_required_api_version()):
            err_msg = (
                f'Extension "{self.extension_id}" requires API version {self.get_required_api_version()}, '
                f'but the current API version is: {API_VERSION})'
            )
            raise ExtensionManifestError(err_msg, ExtensionError.Incompatible)


def read_manifest(extension_id, extensions_dir):
    with open(os.path.join(extensions_dir, extension_id, 'manifest.json'), 'r') as f:
        return load(f)
