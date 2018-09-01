class Response:
    """
    :param ~ulauncher.api.shared.event.BaseEvent event:
    :param ~ulauncher.api.shared.action.BaseAction.BaseAction action:
    """

    event = None

    action = None

    def __init__(self, event, action):
        self.event = event
        self.action = action
