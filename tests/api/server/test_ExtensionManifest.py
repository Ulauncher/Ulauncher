import os
import pytest
from ulauncher.api.shared.errors import ErrorName
from ulauncher.api.server.ExtensionManifest import (ExtensionManifest, ExtensionManifestError)


class TestExtensionManifest:

    @pytest.fixture
    def ext_dir(self):
        return os.path.dirname(os.path.abspath(__file__))

    @pytest.fixture
    def valid_manifest(self):
        return {
            "required_api_version": "1",
            "name": "Timer",
            "description": "Countdown timer with notifications",
            "developer_name": "Aleksandr Gornostal",
            "icon": "images/timer.png"
        }

    def test_open__manifest_file__is_read(self, ext_dir):
        manifest = ExtensionManifest.open('test_extension', ext_dir)
        assert manifest.get_name() == "Test Extension"

    def test_refresh__name__is_reloaded(self, ext_dir):
        manifest = ExtensionManifest('test_extension', {'name': 'Old'}, ext_dir)
        assert manifest.get_name() == 'Old'
        manifest.refresh()
        assert manifest.get_name() == "Test Extension"

    def test_load_icon__load_image__is_called(self, ext_dir, mocker):
        load_image = mocker.patch('ulauncher.api.server.ExtensionManifest.load_image')
        manifest = ExtensionManifest('test_extension', {'icon': 'images/icon.png'}, ext_dir)
        assert manifest.load_icon(100) is load_image.return_value
        load_image.assert_called_with(os.path.join(ext_dir, 'test_extension', 'images/icon.png'), 100)

    def test_validate__name_empty__exception_raised(self, ext_dir):
        manifest = ExtensionManifest('test_extension', {'required_api_version': '1'}, ext_dir)
        with pytest.raises(ExtensionManifestError) as e:
            manifest.validate()
        assert e.value.error_name == ErrorName.InvalidManifestJson.value

    def test_validate__valid_manifest__no_exceptions_raised(self, ext_dir, valid_manifest):
        manifest = ExtensionManifest('test_extension', valid_manifest, ext_dir)
        manifest.validate()

    def test_validate__prefs_empty_id__exception_raised(self, ext_dir, valid_manifest):
        valid_manifest['preferences'] = [
            {}
        ]
        manifest = ExtensionManifest('test_extension', valid_manifest, ext_dir)
        with pytest.raises(ExtensionManifestError) as e:
            manifest.validate()
        assert e.value.error_name == ErrorName.InvalidManifestJson.value

    def test_validate__prefs_incorrect_type__exception_raised(self, ext_dir, valid_manifest):
        valid_manifest['preferences'] = [
            {'id': 'id', 'type': 'incorrect'}
        ]
        manifest = ExtensionManifest('test_extension', valid_manifest, ext_dir)
        with pytest.raises(ExtensionManifestError) as e:
            manifest.validate()
        assert e.value.error_name == ErrorName.InvalidManifestJson.value

    def test_validate__type_kw_empty_name__exception_raised(self, ext_dir, valid_manifest):
        valid_manifest['preferences'] = [
            {'id': 'id', 'type': 'incorrect', 'keyword': 'kw'}
        ]
        manifest = ExtensionManifest('test_extension', valid_manifest, ext_dir)
        with pytest.raises(ExtensionManifestError) as e:
            manifest.validate()
        assert e.value.error_name == ErrorName.InvalidManifestJson.value

    def test_validate__raises_error_if_empty_default_value_for_keyword(self, ext_dir, valid_manifest):
        valid_manifest['preferences'] = [
            {'id': 'id', 'type': 'keyword', 'name': 'My Keyword'}
        ]
        manifest = ExtensionManifest('test_extension', valid_manifest, ext_dir)
        with pytest.raises(ExtensionManifestError) as e:
            manifest.validate()
        assert e.value.error_name == ErrorName.InvalidManifestJson.value

    def test_validate__doesnt_raise_if_empty_default_value_for_non_keyword(self, ext_dir, valid_manifest):
        valid_manifest['preferences'] = [
            {'id': 'id', 'type': 'keyword', 'name': 'My Keyword', 'default_value': 'kw'},
            {'id': 'city', 'type': 'input', 'name': 'City'},
        ]
        manifest = ExtensionManifest('test_extension', valid_manifest, ext_dir)
        manifest.validate()

    def test_check_compatibility__required_api_version_2__exception_raised(self, ext_dir):
        manifest = ExtensionManifest('test_extension', {'required_api_version': '3'}, ext_dir)
        with pytest.raises(ExtensionManifestError) as e:
            manifest.check_compatibility()
        assert e.value.error_name == ErrorName.ExtensionCompatibilityError.value

    def test_check_compatibility__manifest_version_12__exception_raised(self, ext_dir):
        manifest = ExtensionManifest('test_extension', {'required_api_version': '0'}, ext_dir)
        with pytest.raises(ExtensionManifestError) as e:
            manifest.check_compatibility()
        assert e.value.error_name == ErrorName.ExtensionCompatibilityError.value

    def test_check_compatibility__required_api_version_1__no_exceptions(self, ext_dir):
        manifest = ExtensionManifest('test_extension', {'required_api_version': '2'}, ext_dir)
        manifest.check_compatibility()

    def test_get_preference(self, ext_dir):
        manifest_dict = {
            'preferences': [
                {'id': 'myid', 'type': 'keyword', 'default_value': 'mi', 'name': "Mimimi"},
                {'id': 'newid', 'type': 'input', 'default_value': 'ni'}
            ]
        }
        manifest = ExtensionManifest('test_extension', manifest_dict, ext_dir)
        assert manifest.get_preference('newid') == {'id': 'newid', 'type': 'input', 'default_value': 'ni'}

    def test_get_option__option_exists__value_returned(self, ext_dir):
        manifest_dict = {
            'options': {'query_debounce': 0.5}
        }
        manifest = ExtensionManifest('test_extension', manifest_dict, ext_dir)
        assert manifest.get_option('query_debounce') == 0.5

    def test_get_option__option_doesnt_exist__default_returned(self, ext_dir):
        manifest_dict = {
            'options': {}
        }
        manifest = ExtensionManifest('test_extension', manifest_dict, ext_dir)
        assert manifest.get_option('query_debounce', 0.4) == 0.4
