from time import sleep
import pytest
import mock
import pyinotify
from ulauncher.search.apps.AppDb import AppDb
from ulauncher.search.apps.app_watcher import AppNotifyEventHandler


class TestAppNotifyEventHandler:

    @pytest.fixture
    def db(self):
        return mock.create_autospec(AppDb)

    @pytest.fixture
    def event_handler(self, db):
        AppNotifyEventHandler.RETRY_INTERVAL = 0.05
        AppNotifyEventHandler.RETRY_TIME_SPAN = (0, 30)
        return AppNotifyEventHandler(db)

    @pytest.fixture
    def event(self, mocker):
        event = mock.create_autospec(pyinotify.Event)
        event.pathname = 'file.desktop'
        find_desktop_files = mocker.patch('ulauncher.search.apps.app_watcher.find_desktop_files')
        find_desktop_files.return_value = [event.pathname]
        return event

    @pytest.fixture(autouse=True)
    def app(self, mocker):
        read_desktop_file = mocker.patch('ulauncher.search.apps.app_watcher.read_desktop_file')
        return read_desktop_file.return_value

    @pytest.fixture(autouse=True)
    def filter_app(self, mocker):
        filter_app = mocker.patch('ulauncher.search.apps.app_watcher.filter_app')
        filter_app.return_value = True
        return filter_app

    def test_add_file_deferred_retries_several_times(self, db, app, mocker):
        filter_app = mocker.patch('ulauncher.search.apps.app_watcher.filter_app')
        filter_app.return_value = False  # this will make _add_file_sync fail at first

        find_desktop_files = mocker.patch('ulauncher.search.apps.app_watcher.find_desktop_files')
        find_desktop_files.return_value = ['mypath']

        AppNotifyEventHandler.RETRY_INTERVAL = 0.05
        AppNotifyEventHandler.RETRY_TIME_SPAN = (0, 30)
        event_handler = AppNotifyEventHandler(db)
        event_handler.add_file_deferred('mypath')
        sleep(.1)
        assert not db.put_app.called
        filter_app.return_value = True  # now file should be added successfully
        sleep(.2)
        db.put_app.assert_called_with(app)

    def test_add_file_deferred_skip_desktop_file(self, db, app, mocker):
        find_desktop_files = mocker.patch('ulauncher.search.apps.app_watcher.find_desktop_files')
        find_desktop_files.return_value = []

        AppNotifyEventHandler.RETRY_INTERVAL = 0.05
        AppNotifyEventHandler.RETRY_TIME_SPAN = (0, 30)
        event_handler = AppNotifyEventHandler(db)
        event_handler.add_file_deferred('mypath')
        sleep(.1)
        assert not db.put_app.called

    def test_on_created_add_app(self, event_handler, event, db, app):
        event_handler.process_IN_CREATE(event)
        sleep(.06)
        db.put_app.assert_called_with(app)

    def test_on_created_dont_add(self, event_handler, event, db):
        """
        Don't add file if it's not a desktop file
        """
        event.pathname = 'file.desk'
        event_handler.process_IN_CREATE(event)
        assert not db.put_app.called

    def test_on_deleted(self, event_handler, event, db):
        event_handler.process_IN_DELETE(event)
        db.remove_by_path.assert_called_with('file.desktop')

    def test_on_deleted_dont_delete(self, event_handler, event, db):
        event.pathname = 'file.desk'
        event_handler.process_IN_DELETE(event)
        assert not db.remove_by_path.called

    def test_on_modified(self, event_handler, event, db, app):
        event_handler.process_IN_MODIFY(event)
        sleep(.06)
        db.put_app.assert_called_with(app)

    def test_on_modified_dont_modify(self, event_handler, event, db):
        event.pathname = 'file.desk'
        event_handler.process_IN_MODIFY(event)
        assert not db.put_app.called

    def test_on_moved_from(self, event_handler, event, db):
        event_handler.process_IN_MOVED_FROM(event)
        db.remove_by_path.assert_called_with('file.desktop')

    def test_on_moved_to(self, event_handler, event, db, app):
        event_handler.process_IN_MOVED_TO(event)
        sleep(.06)
        db.put_app.assert_called_with(app)
