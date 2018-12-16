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

    @pytest.fixture(autouse=True)
    def app_db(self, mocker):
        app_db = mocker.patch('ulauncher.search.apps.AppDb.AppDb').get_instance.return_value

        def get_by_path(path):
            return {
                'desktop_file': path,
                'name': 'name_%s' % path,
                'description': 'description_%s' % path,
                'icon': 'icon'
            }

        app_db.get_by_path.side_effect = get_by_path
        return app_db

    def test_inc_count(self, db):
        assert db.find('file4.desktop') == 6
        db.inc_count('file4.desktop')
        assert db.find('file4.desktop') == 7

    def test_get_most_frequent(self, db, AppResultItem):
        assert len(db.get_most_frequent(limit=3)) == 3
        for i, file_id in enumerate([4, 3, 6]):
            arg0 = AppResultItem.call_args_list[i][0][0]
            assert arg0['desktop_file'] == 'file%s.desktop' % file_id
