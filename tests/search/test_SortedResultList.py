import mock
import pytest
from ulauncher.search.SortedResultList import SortedResultList
from ulauncher.ext.ResultItem import ResultItem


class TestSortedResultList:

    @pytest.fixture
    def string_score(self, mocker):
        string_score = mocker.patch('ulauncher.search.SortedResultList.string_score')
        string_score.return_value = 0
        return string_score

    @pytest.fixture
    def res_list(self):
        return SortedResultList('bro', min_score=40, limit=3)

    def result_item(self):
        return mock.create_autospec(ResultItem)

    def test_append_uses_string_score(self, res_list, string_score):
        ri1 = self.result_item()
        string_score.return_value = 41
        res_list.append(ri1)
        assert ri1 in res_list
        string_score.assert_called_with('bro', ri1.get_keyword.return_value)

        ri2 = self.result_item()
        ri2.get_keyword.return_value = None
        string_score.return_value = 12
        res_list.append(ri2)
        assert ri2 not in res_list
        string_score.assert_called_with('bro', ri2.get_name.return_value)

    def test_append_maintains_limit(self, res_list, string_score):
        string_score.return_value = 50

        ri1 = self.result_item()
        res_list.append(ri1)
        assert len(res_list) == 1
        assert ri1 in res_list

        ri2 = self.result_item()
        res_list.append(ri2)
        assert len(res_list) == 2
        assert ri2 in res_list

        string_score.return_value = 42
        ri3 = self.result_item()
        res_list.append(ri3)
        assert len(res_list) == 3
        assert ri3 in res_list

        ri4 = self.result_item()
        string_score.return_value = 39
        res_list.append(ri4)
        assert len(res_list) == 3
        assert ri4 not in res_list  # doesn't get appended because 39 < min_score /40/

        ri5 = self.result_item()
        string_score.return_value = 100
        res_list.append(ri5)
        assert len(res_list) == 3
        assert ri5 in res_list
        assert ri3 not in res_list  # ri3 gets removed because of the lowest score (42)

        string_score.return_value = 80
        ri6 = self.result_item()
        res_list.append(ri6)
        assert len(res_list) == 3
        assert ri6 in res_list

        assert res_list[0] == ri5  # ri5 stays first, because it has the highest score (100)
