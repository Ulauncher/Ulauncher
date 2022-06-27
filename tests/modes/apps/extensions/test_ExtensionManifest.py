import os
import pytest
from ulauncher.api.shared.errors import ExtensionError
from ulauncher.modes.extensions.ExtensionManifest import ExtensionManifest, ExtensionManifestError


class TestExtensionManifest:

    @pytest.fixture
    def valid_manifest(self):
        return {
            "required_api_version": "1",
            "name": "Timer",
            "description": "Countdown timer with notifications",
            "developer_name": "Aleksandr Gornostal",
            "icon": "images/timer.png",
            "preferences": [{
                "id": "keyword",
                "type": "keyword",
                "name": "Timer",
                "default_value": "ti"
            }]
        }

    def test_open__manifest_file__is_read(self):
        ext_dir = os.path.dirname(os.path.abspath(__file__))
        manifest = ExtensionManifest.open('test_extension', ext_dir)
        assert manifest.get_name() == "Test Extension"

    def test_validate__name_empty__exception_raised(self):
        manifest = ExtensionManifest({"required_api_version": "1"})
        with pytest.raises(ExtensionManifestError) as e:
            manifest.validate()
        assert e.value.error_name == ExtensionError.InvalidManifest.value

    def test_validate__valid_manifest__no_exceptions_raised(self, valid_manifest):
        manifest = ExtensionManifest(valid_manifest)
        manifest.validate()

    def test_validate__prefs_empty_id__exception_raised(self, valid_manifest):
        valid_manifest['preferences'] = [{}]
        manifest = ExtensionManifest(valid_manifest)
        with pytest.raises(ExtensionManifestError) as e:
            manifest.validate()
        assert e.value.error_name == ExtensionError.InvalidManifest.value

    def test_validate__prefs_incorrect_type__exception_raised(self, valid_manifest):
        valid_manifest['preferences'] = [
            {'id': 'id', 'type': 'incorrect'}
        ]
        manifest = ExtensionManifest(valid_manifest)
        with pytest.raises(ExtensionManifestError) as e:
            manifest.validate()
        assert e.value.error_name == ExtensionError.InvalidManifest.value

    def test_validate__type_kw_empty_name__exception_raised(self, valid_manifest):
        valid_manifest['preferences'] = [
            {'id': 'id', 'type': 'incorrect', 'keyword': 'kw'}
        ]
        manifest = ExtensionManifest(valid_manifest)
        with pytest.raises(ExtensionManifestError) as e:
            manifest.validate()
        assert e.value.error_name == ExtensionError.InvalidManifest.value

    def test_validate__raises_error_if_empty_default_value_for_keyword(self, valid_manifest):
        valid_manifest['preferences'] = [
            {'id': 'id', 'type': 'keyword', 'name': 'My Keyword'}
        ]
        manifest = ExtensionManifest(valid_manifest)
        with pytest.raises(ExtensionManifestError) as e:
            manifest.validate()
        assert e.value.error_name == ExtensionError.InvalidManifest.value

    def test_validate__doesnt_raise_if_empty_default_value_for_non_keyword(self, valid_manifest):
        valid_manifest['preferences'] = [
            {'id': 'id', 'type': 'keyword', 'name': 'My Keyword', 'default_value': 'kw'},
            {'id': 'city', 'type': 'input', 'name': 'City'},
        ]
        manifest = ExtensionManifest(valid_manifest)
        manifest.validate()

    def test_check_compatibility__required_api_version_2__exception_raised(self):
        manifest = ExtensionManifest({"name": "Test", "required_api_version": "3"})
        with pytest.raises(ExtensionManifestError) as e:
            manifest.check_compatibility()
        assert e.value.error_name == ExtensionError.Incompatible.value

    def test_check_compatibility__manifest_version_12__exception_raised(self):
        manifest = ExtensionManifest({"name": "Test", "required_api_version": "0"})
        with pytest.raises(ExtensionManifestError) as e:
            manifest.check_compatibility()
        assert e.value.error_name == ExtensionError.Incompatible.value

    def test_check_compatibility__required_api_version_1__no_exceptions(self):
        manifest = ExtensionManifest({"name": "Test", "required_api_version": "2"})
        manifest.check_compatibility()

    def test_get_option__option_exists__value_returned(self):
        manifest = ExtensionManifest({"options": {"query_debounce": 0.5}})
        assert manifest.get_option("query_debounce") == 0.5

    def test_get_option__option_doesnt_exist__default_returned(self):
        manifest = ExtensionManifest({"options": {}})
        assert manifest.get_option('query_debounce', 0.4) == 0.4
