import mock
import pytest
from ulauncher.api.server.ExtensionRunner import ExtensionRunner, ExtRunErrorName
from ulauncher.api.server.ExtensionServer import ExtensionServer
from ulauncher.api.server.ExtensionManifest import ExtensionManifestError
from ulauncher.api.shared.errors import ErrorName


class TestExtensionRunner:

    @pytest.fixture
    def runner(self, ext_server):
        return ExtensionRunner(ext_server)

    @pytest.fixture
    def ext_server(self):
        return mock.create_autospec(ExtensionServer)

    @pytest.fixture(autouse=True)
    def find_extensions(self, mocker):
        return mocker.patch('ulauncher.api.server.ExtensionRunner.find_extensions')

    @pytest.fixture(autouse=True)
    def get_options(self, mocker):
        return mocker.patch('ulauncher.api.server.ExtensionRunner.get_options')

    @pytest.fixture(autouse=True)
    def ExtensionManifest(self, mocker):
        return mocker.patch('ulauncher.api.server.ExtensionRunner.ExtensionManifest')

    @pytest.fixture
    def manifest(self, ExtensionManifest):
        return ExtensionManifest.open.return_value

    @pytest.fixture(autouse=True)
    def run_async(self, mocker):
        return mocker.patch('ulauncher.api.server.ExtensionRunner.run_async')

    def test_run__incompatible_version__exception_is_raised(self, runner, manifest):
        manifest.check_compatibility.side_effect = ExtensionManifestError(
            'message', ErrorName.ExtensionCompatibilityError)
        with pytest.raises(ExtensionManifestError):
            runner.run('id')

    def test_run__ExtensionManifest_open__is_called(self, runner, ExtensionManifest):
        runner.run('id')
        ExtensionManifest.open.assert_called_with('id')

    def test_run_all__run__called_with_extension_ids(self, runner, mocker, find_extensions):
        mocker.patch.object(runner, 'run')
        find_extensions.return_value = [('id_1', 'path_1'), ('id_2', 'path_2'), ('id_3', 'path_3')]
        runner.run_all()
        runner.run.assert_any_call('id_1')
        runner.run.assert_any_call('id_2')
        runner.run.assert_any_call('id_3')

    def test_set_extension_error(self, runner):
        runner.set_extension_error('id_1', ExtRunErrorName.Terminated, 'message')
        error = runner.get_extension_error('id_1')
        assert error['name'] == ExtRunErrorName.Terminated.value
        assert error['message'] == 'message'
