import os
from json import load
from typing import cast, Optional, List, Union
from ulauncher.config import API_VERSION, EXTENSIONS_DIR
from ulauncher.utils.icon import load_icon
from ulauncher.api.shared.errors import UlauncherAPIError, ErrorName
from ulauncher.utils.version import satisfies
from ulauncher.utils.mypy_extensions import TypedDict


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
        'default_value': str,
        'options': OptionItems,
        'icon': str,
    })
ManifestJson = TypedDict('ManifestJson', {
    'required_api_version': str,
    'name': str,
    'description': str,
    'developer_name': str,
    'icon': str,
    'use_pip_run': bool,
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

    def refresh(self):
        self.manifest = cast(ManifestJson, read_manifest(self.extension_id, self.extensions_dir))

    def get_name(self) -> str:
        return self.manifest['name']

    def get_description(self) -> str:
        return self.manifest['description']

    def get_icon(self) -> str:
        return self.manifest['icon']

    def get_icon_path(self) -> str:
        return os.path.join(self.extensions_dir, self.extension_id, self.get_icon())

    def load_icon(self, size, path=None):
        abs_path = os.path.join(self.extensions_dir, self.extension_id, path) if path else self.get_icon_path()
        return load_icon(abs_path, size)

    def get_required_api_version(self) -> str:
        return self.manifest['required_api_version']

    def get_developer_name(self) -> str:
        return self.manifest['developer_name']

    def get_use_pip_run(self) -> bool:
        return self.manifest.get('use_pip_run', False)

    def get_preferences(self) -> List[ManifestPreferenceItem]:
        return self.manifest.get('preferences', [])

    def get_preference(self, id) -> Optional[ManifestPreferenceItem]:
        for p in self.get_preferences():
            if p['id'] == id:
                return p

        return None

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
                assert p.get('id'), 'Preferences error. Id cannot be empty'
                assert p.get('type'), 'Preferences error. Type cannot be empty'
                assert p.get('type') in ["keyword", "input", "text", "select"], \
                    'Preferences error. Type can be "keyword", "input", "text", or "select"'
                assert p.get('name'), 'Preferences error. Name cannot be empty'
                if p['type'] == 'keyword':
                    assert p.get('default_value'), 'Preferences error. Default value cannot be empty for keyword'
                if p['type'] == 'select':
                    assert isinstance(p.get('options'), list), 'Preferences error. Options must be a list'
                    assert p.get('options'), 'Preferences error. Option list cannot be empty'
        except AssertionError as e:
            raise ExtensionManifestError(str(e), ErrorName.InvalidManifestJson) from e
        except KeyError as e:
            raise ExtensionManifestError(f'{e} is not provided', ErrorName.InvalidManifestJson) from e

    def check_compatibility(self):
        if not satisfies(API_VERSION, self.get_required_api_version()):
            err_msg = (
                f'Extension "{self.extension_id}" requires API version {self.get_required_api_version()}, '
                f'but the current API version is: {API_VERSION})'
            )
            raise ExtensionManifestError(err_msg, ErrorName.ExtensionCompatibilityError)


def read_manifest(extension_id, extensions_dir):
    with open(os.path.join(extensions_dir, extension_id, 'manifest.json'), 'r') as f:
        return load(f)
