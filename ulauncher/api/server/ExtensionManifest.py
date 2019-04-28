import os
from json import load
from ulauncher.config import get_version, EXTENSIONS_DIR
from ulauncher.util.image_loader import load_image


class ExtensionManifest(object):
    """
    Reads `manifest.json`
    """

    @classmethod
    def open(cls, extension_id, extensions_dir=EXTENSIONS_DIR):
        return cls(extension_id, read_manifest(extension_id, extensions_dir), extensions_dir)

    def __init__(self, extension_id, manifest, extensions_dir=EXTENSIONS_DIR):
        self.extensions_dir = extensions_dir
        self.extension_id = extension_id
        self.manifest = manifest

    def refresh(self):
        self.manifest = read_manifest(self.extension_id, self.extensions_dir)

    def get_name(self):
        return self.manifest['name']

    def get_description(self):
        return self.manifest['description']

    def get_icon(self):
        return self.manifest['icon']

    def get_icon_path(self):
        return os.path.join(self.extensions_dir, self.extension_id, self.get_icon())

    def load_icon(self, size):
        return load_image(self.get_icon_path(), size)

    def get_required_api_version(self):
        return self.manifest.get('required_api_version') or self.manifest.get('api_version')

    def get_developer_name(self):
        return self.manifest['developer_name']

    def get_preferences(self):
        return self.manifest.get('preferences', [])

    def get_preference(self, id):
        for p in self.get_preferences():
            if p['id'] == id:
                return p

    def get_option(self, name, default=None):
        try:
            return self.manifest['options'][name]
        except KeyError:
            return default

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
            raise ManifestValidationError(e.message)
        except KeyError as e:
            raise ManifestValidationError('%s is not provided' % e.message)

    def check_compatibility(self):
        app_version = get_version()
        if self.get_required_api_version() != '1':
            raise VersionIncompatibilityError('Extension "%s" is not compatible with Ulauncher v%s' %
                                              (self.extension_id, app_version))


class VersionIncompatibilityError(RuntimeError):
    pass


class ManifestValidationError(Exception):
    pass


def read_manifest(extension_id, extensions_dir):
    with open(os.path.join(extensions_dir, extension_id, 'manifest.json'), 'r') as f:
        return load(f)
