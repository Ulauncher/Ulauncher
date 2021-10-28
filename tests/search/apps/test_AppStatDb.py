import pytest
from ulauncher.search.apps.AppStatDb import AppStatDb


class TestAppStatDb:

    @pytest.fixture
    def db(self):
        db = AppStatDb('test')
        # put some data in
        db.put('file1.desktop', 3)
        db.put('file2.desktop', 1)
        db.put('file3.desktop', 5)
        db.put('file4.desktop', 6)
        db.put('file5.desktop', 2)
        db.put('file6.desktop', 4)
        db.put('file7.desktop', 0)
        return db

    @pytest.fixture(autouse=True)
    def AppResultItem(self, mocker):
        return mocker.patch('ulauncher.search.apps.AppResultItem.AppResultItem')

    def test_inc_count(self, db):
        assert db.find('file4.desktop') == 6
        db.inc_count('file4.desktop')
        assert db.find('file4.desktop') == 7

    def test_get_most_frequent(self, db, AppResultItem):
        assert len(db.get_most_frequent(limit=3)) == 3
        assert db.get_most_frequent(limit=1) == ['file4.desktop']
        assert db.get_most_frequent(limit=3) == ['file4.desktop', 'file3.desktop', 'file6.desktop']
