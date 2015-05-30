from ulauncher.ext.actions.SetUserQueryAction import SetUserQueryAction


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
            return self._action_on_enter(item, query)

    def _action_on_enter(self, item, query_str):
        """
        Returns True if something needs to be rendered
        """
        q = Query(query_str)
        keyword = item.get_keyword()
        is_keyword_misspelled = keyword and q.get_keyword() != keyword

        # in order to use argument, keyword should match item's keyword
        argument = q.get_argument() if not is_keyword_misspelled else None
        action_list = item.on_enter(argument=argument)
        if is_keyword_misspelled:
            action_list.add(SetUserQueryAction('%s ' % keyword))
        action_list.run_all()

        return action_list.keep_app_open()


class Query(object):
    """
    Parses user's query
    """

    def __init__(self, query):
        self.query = query.strip()

    def get_keyword(self):
        return self.query.split(' ', 1)[0]

    def get_argument(self):
        try:
            return self.query.split(' ', 1)[1].strip()
        except IndexError:
            return None
