import pytest
from ulauncher.search.SortedResultList import SortedResultList


class Item(object):

    def __init__(self, name, keyword=None):
        self.name = name
        self.keyword = keyword

    def __repr__(self):
        return '<Item name=%s>' % self.name

    def get_keyword(self):
        return self.keyword

    def get_name(self):
        return self.name


class TestSortedResultList:

    @pytest.fixture
    def result_list(self):
        return SortedResultList('bar', min_score=50, limit=4)

    def test_append__uses_min_score(self, result_list):
        result_list.append(Item('000'))
        assert not len(result_list)

        i = Item('baz')
        result_list.append(i)
        assert i is result_list[0]

    def test_append__uses_limit(self, result_list):
        i = Item('baz')
        result_list.append(i)
        result_list.append(Item('bax'))
        result_list.append(Item('bat'))
        result_list.append(Item('bay'))
        assert len(result_list) == 4
        result_list.append(Item('baf'))
        assert len(result_list) == 4
        assert i not in result_list  # i gets removed

    def test_append__uses_keyword(self, result_list):
        item = Item('000', keyword='baz')
        result_list.append(Item('bad'))
        result_list.append(item)
        assert item in result_list

    def test_collection_is_always_sorted(self, result_list):
        result_list.append(Item('bax'))
        result_list.append(Item('bar'))
        result_list.append(Item('bay'))
        result_list.append(Item('fars'))

        assert result_list[0].get_name() == 'bar'
        assert result_list[-1].get_name() == 'fars'
