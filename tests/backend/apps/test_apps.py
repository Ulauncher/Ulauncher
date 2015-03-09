import pytest
import mock

from ulauncher.backend.apps.AppDb import AppDb
from ulauncher.backend.apps import AppEventHandler
from watchdog import events


class TestAppEventHandler:

    @pytest.fixture
    def db(self):
        return mock.create_autospec(AppDb)

    @pytest.fixture
    def event_handler(self, db):
        return AppEventHandler(db)

    @pytest.fixture
    def file_created_event(self):
        return mock.create_autospec(events.FileCreatedEvent)

    @pytest.fixture
    def file_deleted_event(self):
        return mock.create_autospec(events.FileDeletedEvent)

    @pytest.fixture
    def file_modified_event(self):
        return mock.create_autospec(events.FileModifiedEvent)

    @pytest.fixture
    def file_moved_event(self):
        return mock.create_autospec(events.FileMovedEvent)

    @pytest.fixture(autouse=True)
    def app(self, mocker):
        read_desktop_file = mocker.patch('ulauncher.backend.apps.read_desktop_file')
        return read_desktop_file.return_value

    @pytest.fixture(autouse=True)
    def filter_app(self, mocker):
        filter_app = mocker.patch('ulauncher.backend.apps.filter_app')
        filter_app.return_value = True
        return filter_app

    def test_on_created_add_app(self, event_handler, file_created_event, db, app):
        file_created_event.src_path = 'file.desktop'
        event_handler.on_created(file_created_event)
        db.put_app.assert_called_with(app)

    def test_on_created_dont_add(self, event_handler, file_created_event, db, app):
        """
        Don't add file if it's not a desktop file
        """
        file_created_event.src_path = 'file.desk'
        event_handler.on_created(file_created_event)
        assert not db.put_app.called

    def test_on_deleted(self, event_handler, file_deleted_event, db, app):
        file_deleted_event.src_path = 'file.desktop'
        event_handler.on_deleted(file_deleted_event)
        db.remove.assert_called_with('file.desktop')

    def test_on_deleted_dont_delete(self, event_handler, file_deleted_event, db, app):
        file_deleted_event.src_path = 'file.desk'
        event_handler.on_deleted(file_deleted_event)
        assert not db.remove.called

    def test_on_modified(self, event_handler, file_modified_event, db, app):
        file_modified_event.src_path = 'file.desktop'
        event_handler.on_modified(file_modified_event)
        db.put_app.assert_called_with(app)

    def test_on_modified_dont_modify(self, event_handler, file_modified_event, db, app):
        file_modified_event.src_path = 'file.desk'
        event_handler.on_modified(file_modified_event)
        assert not db.put_app.called

    def test_on_moved(self, event_handler, file_moved_event, db, app):
        file_moved_event.src_path = 'file_old.desktop'
        file_moved_event.dest_path = 'file_new.desktop'
        event_handler.on_moved(file_moved_event)
        db.remove.assert_called_with('file_old.desktop')
        db.put_app.assert_called_with(app)

    def xtest_on_moved_dont_update(self, event_handler, file_moved_event, db, app):
        file_moved_event.src_path = 'file.desk'
        file_moved_event.dest_path = 'file.desk'
        event_handler.on_moved(file_modified_event)
        assert not db.remove.called
        assert not db.put_app.called
