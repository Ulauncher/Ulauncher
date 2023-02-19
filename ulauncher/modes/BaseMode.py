from ulauncher.api.shared.action.DoNothingAction import DoNothingAction


class BaseMode:
    # pylint: disable=unused-argument
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
        :param Gdk.Widget widget:
        :param Gdk.EventKey event:
        :param ~ulauncher.api.shared.query.Query query:
        :rtype: :class:`BaseAction`
        """
        return DoNothingAction()

    def handle_query(self, query):
        """
        :rtype: list of Results
        """
        return []

    def get_triggers(self):
        """
        Returns an iterable of searchable results
        """
        return []

    def get_fallback_results(self):
        """
        Returns a list of fallback results to
        be displayed if nothing matches the user input
        """
        return []
