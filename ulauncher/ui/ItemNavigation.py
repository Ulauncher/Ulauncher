from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
from ulauncher.modes.QueryHistoryDb import QueryHistoryDb

query_history = QueryHistoryDb.get_instance()


class ItemNavigation:
    """
    Performs navigation through found results
    """

    def __init__(self, items):
        """
        :param list items: list of ResultWidget()'s
        """
        self.items = items
        self.items_num = len(items)
        self.selected = None

    def get_default(self, query):
        """
        Gets the index of the result that should be selected (0 by default)
        """
        previous_pick = query_history.find(query)

        for index, item in enumerate(self.items):
            result = item.item_object
            if result.searchable and result.get_name() == previous_pick:
                return index
        return 0

    def select_default(self, query):
        self.select(self.get_default(query))

    def select(self, index):
        if not 0 < index < self.items_num:
            index = 0

        if self.selected is not None:
            self.items[self.selected].deselect()

        self.selected = index
        self.items[index].select()

    def go_up(self):
        index = self.selected - 1 if self.selected is not None and self.selected > 0 else self.items_num - 1
        self.select(index)

    def go_down(self):
        index = self.selected + 1 if self.selected is not None and self.selected < self.items_num else 0
        self.select(index)

    def enter(self, query, index=None, alt=False):
        """
        Enter into selected item, unless 'index' is passed
        Return boolean - True if Ulauncher window should be closed
        """
        if index is not None:
            if not 0 <= index < self.items_num:
                raise IndexError

            self.select(index)
            return self.enter(query)

        if self.selected is not None:
            item = self.items[self.selected]
            result = item.item_object
            if not alt and result.searchable:
                query_history.save_query(str(query), result.get_name())

            action = item.on_enter(query) if not alt else item.on_alt_enter(query)
            if not action:
                return True
            if isinstance(action, list):
                action = RenderResultListAction(action)
            action.run()
            return action.keep_app_open()

        return None
