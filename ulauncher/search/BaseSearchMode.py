from ulauncher.api.shared.action.DoNothingAction import DoNothingAction


class BaseSearchMode(object):

    def is_enabled(self, query):
        """
        Return True if mode should be enabled for a query
        """
        return False

    def on_query_change(self, query):
        """
        Triggered when user changes a search query
        """

    def handle_key_press_event(self, widget, event, query):
        """
        @param widget Gdk.Widget
        @param event Gdk.EventKey
        @param query Query
        @return Action object
        """
        return DoNothingAction()

    def handle_query(self, query):
        """
        @return Action Object
        """
        return DoNothingAction()

    def get_default_items(self):
        """
        Returns a list of default result items that
        should be displayed if no results found
        """
        return []

    def get_searchable_items(self):
        """
        Returns a list of result items that
        can be looked up by name or keyword
        """
        return []
