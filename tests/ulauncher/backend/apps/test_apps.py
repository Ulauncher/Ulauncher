import pytest
import mock
import pyinotify

from ulauncher.backend.apps.AppDb import AppDb
from ulauncher.backend.apps import InotifyEventHandler


class TestInotifyEventHandler:

    @pytest.fixture
    def db(self):
        return mock.create_autospec(AppDb)

    @pytest.fixture
    def event_handler(self, db):
        return InotifyEventHandler(db)

    @pytest.fixture
    def event(self):
        event = mock.create_autospec(pyinotify.Event)
        event.pathname = 'file.desktop'
        return event

    @pytest.fixture(autouse=True)
    def app(self, mocker):
        read_desktop_file = mocker.patch('ulauncher.backend.apps.read_desktop_file')
        return read_desktop_file.return_value

    @pytest.fixture(autouse=True)
    def filter_app(self, mocker):
        filter_app = mocker.patch('ulauncher.backend.apps.filter_app')
        filter_app.return_value = True
        return filter_app

    def test_on_created_add_app(self, event_handler, event, db, app):
        event_handler.process_IN_CREATE(event)
        db.put_app.assert_called_with(app)

    def test_on_created_dont_add(self, event_handler, event, db, app):
        """
        Don't add file if it's not a desktop file
        """
        event.pathname = 'file.desk'
        event_handler.process_IN_CREATE(event)
        assert not db.put_app.called

    def test_on_deleted(self, event_handler, event, db, app):
        event_handler.process_IN_DELETE(event)
        db.remove_by_path.assert_called_with('file.desktop')

    def test_on_deleted_dont_delete(self, event_handler, event, db, app):
        event.pathname = 'file.desk'
        event_handler.process_IN_DELETE(event)
        assert not db.remove_by_path.called

    def test_on_modified(self, event_handler, event, db, app):
        event_handler.process_IN_MODIFY(event)
        db.put_app.assert_called_with(app)

    def test_on_modified_dont_modify(self, event_handler, event, db, app):
        event.pathname = 'file.desk'
        event_handler.process_IN_MODIFY(event)
        assert not db.put_app.called

    def test_on_moved_from(self, event_handler, event, db, app):
        event_handler.process_IN_MOVED_FROM(event)
        db.remove_by_path.assert_called_with('file.desktop')

    def test_on_moved_to(self, event_handler, event, db, app):
        event_handler.process_IN_MOVED_TO(event)
        db.put_app.assert_called_with(app)
