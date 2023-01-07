from ulauncher.api.shared.action.BaseAction import BaseAction


class DoNothingAction(BaseAction):
    """
    Does nothing. Keeps Ulauncher window open
    """

    keep_app_open = True

    def run(self):
        pass
