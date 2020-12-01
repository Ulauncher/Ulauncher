from ulauncher.api.shared.item.ResultItem import ResultItem
from ulauncher.search.SortedList import SortedList


class TestSortedListOrder:
    def test_order_if_name_and_description_match(self):
        app_name_1 = 'Problem Reporting'
        app_name_2 = 'VS Code'
        r1 = ResultItem(name=app_name_1, description='An application to report problems')
        r2 = ResultItem(name=app_name_2, description='Code editing, redefined')

        sorted_list_instance = SortedList(query='re', min_score=50, limit=10)
        sorted_list_instance.append(r1)
        sorted_list_instance.append(r2)
        assert sorted_list_instance[0].get_name() == app_name_1

        # TODO: Need to investigate why the sorted list instance is 1, even after appending two items
        assert len(sorted_list_instance) == 2
        assert sorted_list_instance[1].get_name() == app_name_2
