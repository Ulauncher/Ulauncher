from .BaseAction import BaseAction


class DoNothingAction(BaseAction):
    """
    Does nothing. Keeps Ulauncher window open
    """

    def keep_app_open(self):
        return True

    def run(self):
        pass
