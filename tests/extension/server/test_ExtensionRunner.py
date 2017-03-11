import mock
import pytest
from ulauncher.extension.server.ExtensionRunner import ExtensionRunner
from ulauncher.extension.server.ExtensionManifest import VersionIncompatibilityError


class TestExtensionRunner:

    @pytest.fixture(autouse=True)
    def find_extensions(self, mocker):
        return mocker.patch('ulauncher.extension.server.ExtensionRunner.find_extensions')

    @pytest.fixture(autouse=True)
    def parse_options(self, mocker):
        return mocker.patch('ulauncher.extension.server.ExtensionRunner.parse_options')

    @pytest.fixture(autouse=True)
    def ExtensionManifest(self, mocker):
        return mocker.patch('ulauncher.extension.server.ExtensionRunner.ExtensionManifest')

    @pytest.fixture
    def manifest(self, ExtensionManifest):
        return ExtensionManifest.open.return_value

    @pytest.fixture(autouse=True)
    def run_async(self, mocker):
        return mocker.patch('ulauncher.extension.server.ExtensionRunner.run_async')

    def test_run__incompatible_version__exception_is_raised(self, manifest):
        manifest.check_compatibility.side_effect = VersionIncompatibilityError()
        runner = ExtensionRunner()
        with pytest.raises(VersionIncompatibilityError):
            runner.run('id')

    def test_run__ExtensionManifest_open__is_called(self, ExtensionManifest):
        runner = ExtensionRunner()
        runner.run('id')
        ExtensionManifest.open.assert_called_with('id')

    def test_run_all__run__called_with_extension_ids(self, mocker, find_extensions):
        runner = ExtensionRunner()
        mocker.patch.object(runner, 'run')
        find_extensions.return_value = [('id_1', 'path_1'), ('id_2', 'path_2'), ('id_3', 'path_3')]
        runner.run_all()
        runner.run.assert_any_call('id_1')
        runner.run.assert_any_call('id_2')
        runner.run.assert_any_call('id_3')
