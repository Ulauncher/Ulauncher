class SearchMode(object):

    def is_enabled(self, query):
        """
        Return True if mode should be enabled for a query
        """
        return False

    def on_key_press_event(self, widget, event, query):
        """
        @param widget Gdk.Widget
        @param event Gdk.EventKey
        @param query Query
        @return iterable with ActionList objects
        """

    def on_query(self, query):
        """
        @return iterable with ActionList objects
        """
