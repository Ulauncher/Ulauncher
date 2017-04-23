
class EventListener(object):
    """
    Base event listener class
    """

    def on_event(self, event, extension):
        """
        :param ~ulauncher.api.shared.event.BaseEvent event:
        :param ~ulauncher.api.client.Extension.Extension extension:

        :rtype: ~ulauncher.api.shared.action.BaseAction.BaseAction or None
        :return: Instance of `BaseAction` if needed
        """
        pass
