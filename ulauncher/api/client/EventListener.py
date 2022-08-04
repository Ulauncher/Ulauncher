class EventListener:
    """
    Base event listener class
    """

    def on_event(self, event, extension):
        """
        :param ~ulauncher.api.shared.event.BaseEvent event: event that listener was subscribed to
        :param ~ulauncher.api.Extension extension:

        :rtype: :class:`~ulauncher.api.shared.action.BaseAction.BaseAction` or None
        :return: Instance of :class:`BaseAction` or :code:`None`
        """
