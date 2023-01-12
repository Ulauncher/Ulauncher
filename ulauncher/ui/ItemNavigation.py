from ulauncher.api.shared.action.BaseAction import BaseAction
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
from ulauncher.config import PATHS
from ulauncher.utils.json_data import JsonData

query_history = JsonData.new_from_file(f"{PATHS.STATE}/query_history.json")


class ItemNavigation:
    """
    Performs navigation through found results
    """

    def __init__(self, result_widgets):
        """
        :param list result_widgets: list of ResultWidget()'s
        """
        self.result_widgets = result_widgets
        self.selected = None

    def get_default(self, query):
        """
        Gets the index of the result that should be selected (0 by default)
        """
        previous_pick = query_history.get(query)

        for index, widget in enumerate(self.result_widgets):
            if widget.result.searchable and widget.result.get_name() == previous_pick:
                return index
        return 0

    def select_default(self, query):
        self.select(self.get_default(query))

    def select(self, index):
        if not 0 < index < len(self.result_widgets):
            index = 0

        if self.selected is not None:
            self.result_widgets[self.selected].deselect()

        self.selected = index
        self.result_widgets[index].select()

    def go_up(self):
        self.select((self.selected or len(self.result_widgets)) - 1)

    def go_down(self):
        next = (self.selected or 0) + 1
        self.select(next if next < len(self.result_widgets) else 0)

    def enter(self, query, index=None, alt=False):
        """
        Enter into selected item, unless 'index' is passed
        Return boolean - True if Ulauncher window should be closed
        """
        if index is not None:
            if not 0 <= index < len(self.result_widgets):
                raise IndexError

            self.select(index)
            return self.enter(query)

        if self.selected is not None:
            result = self.result_widgets[self.selected].result
            if query and not alt and result.searchable:
                query_history.save({str(query): result.get_name()})

            action = result.on_enter(query) if not alt else result.on_alt_enter(query)
            if not action:
                return True
            if isinstance(action, list) and not isinstance(action, BaseAction):
                action = RenderResultListAction(action)
            action.run()
            return not action.keep_app_open

        return None
