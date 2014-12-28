
class Navigation(object):
    """
    Performs navigation through found results
    """

    def __init__(self, items):
        """
        :param [ResultItem] items:
        """
        self.items = items
        self.items_num = len(items)
        self.selected = None

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

    def enter(self, index=None):
        """
        Enter into selected item, unless 'index' is passed
        """
        if index:
            if not (0 < index < self.items_num):
                raise IndexError

            self.select(index)
            return self.enter()
        elif self.selected is not None:
            return self.items[self.selected].enter()
