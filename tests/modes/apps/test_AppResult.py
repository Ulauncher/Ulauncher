import pathlib
import shutil
import pytest
from gi.repository import Gio
from ulauncher.utils.json_data import JsonData
from ulauncher.modes.apps.AppResult import AppResult
from ulauncher.api.shared.query import Query

# Note: These mock apps actually need real values for Exec or Icon, or they won't load,
# and they need to load from actual files or get_id() and get_filename() will return None
ENTRIES_DIR = pathlib.Path(__file__).parent.joinpath("mock_desktop_entries").resolve()


def teardown_module(module):
    shutil.rmtree("/tmp/ulauncher-test")


class TestAppResult:
    @pytest.fixture(autouse=True)
    def patch_DesktopAppInfo_new(self, mocker):
        def mkappinfo(app_id):
            return Gio.DesktopAppInfo.new_from_filename(f"{ENTRIES_DIR}/{app_id}")

        return mocker.patch("ulauncher.modes.apps.AppResult.Gio.DesktopAppInfo.new", new=mkappinfo)

    @pytest.fixture(autouse=True)
    def patch_DesktopAppInfo_get_all(self, mocker):
        def get_all_appinfo():
            return map(Gio.DesktopAppInfo.new, ["trueapp.desktop", "falseapp.desktop"])

        return mocker.patch("ulauncher.modes.apps.AppResult.Gio.DesktopAppInfo.get_all", new=get_all_appinfo)

    @pytest.fixture
    def app1(self):
        return AppResult.from_id("trueapp.desktop")

    @pytest.fixture
    def app2(self):
        return AppResult.from_id("falseapp.desktop")

    @pytest.fixture(autouse=True)
    def app_starts(self, mocker):
        app_starts = JsonData.new_from_file("/tmp/ulauncher-test/app_starts.json")
        app_starts.update({"falseapp.desktop": 3000, "trueapp.desktop": 765})
        return mocker.patch("ulauncher.modes.apps.AppResult.app_starts", new=app_starts)

    def test_get_name(self, app1):
        assert app1.name == "TrueApp - Full Name"

    def test_get_description(self, app1):
        assert app1.get_description(Query("q")) == "Your own yes-man"

    def test_icon(self, app1):
        assert app1.icon == "dialog-yes"

    def test_search_score(self, app1):
        assert app1.search_score("true") > app1.search_score("trivago")

    def test_on_enter(self, app1, mocker, app_starts):
        launch_app = mocker.patch("ulauncher.modes.apps.AppResult.launch_app")
        assert app1.on_enter(Query("query")) is launch_app.return_value
        launch_app.assert_called_with("trueapp.desktop")
        assert app_starts.get("trueapp.desktop") == 766

    def test_get_most_frequent(self):
        assert len(AppResult.get_most_frequent()) == 2
        assert AppResult.get_most_frequent()[0].name == "FalseApp - Full Name"
