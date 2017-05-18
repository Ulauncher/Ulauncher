class ItemNavigation(object):
    """
    Performs navigation through found results
    """

    def __init__(self, items):
        """
        :param list items: list of ResultItemWidget()'s
        """
        self.items = items
        self.items_num = len(items)
        self.selected = None

    def get_selected_index(self):
        return self.selected

    def select_default(self, query):
        """
        Selects item that should be selected by default
        If no such items found, select the first one in the list
        """
        self.select(next((index for index, item in enumerate(self.items) if item.selected_by_default(query)), 0))

    def select(self, index):
        if not (0 < index < self.items_num):
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
            if not (0 <= index < self.items_num):
                raise IndexError

            self.select(index)
            return self.enter(query)
        elif self.selected is not None:
            item = self.items[self.selected]
            action = item.on_enter(query) if not alt else item.on_alt_enter(query)
            if not action:
                return True
            action.run()
            return action.keep_app_open()
