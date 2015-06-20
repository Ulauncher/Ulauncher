from ulauncher.ext.actions.SetUserQueryAction import SetUserQueryAction
from ulauncher.ext.Query import Query


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

    def get_selected_name(self):
        index = self.get_selected_index()
        return self.items[index].get_name()

    def get_index_by_name(self, name):
        return next((index for index, item in enumerate(self.items) if item.get_name() == name), None)

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

    def enter(self, query, index=None):
        """
        Enter into selected item, unless 'index' is passed
        Return boolean - True if Ulauncher window should be closed
        """
        if index:
            if not (0 < index < self.items_num):
                raise IndexError

            self.select(index)
            return self.enter(query)
        elif self.selected is not None:
            item = self.items[self.selected]
            action_list = item.on_enter(query)
            action_list.run_all()
            return action_list.keep_app_open()
