from .BaseAction import BaseAction


class HideWindowAction(BaseAction):
    """
    Does what the class name says
    """

    def keep_app_open(self):
        return False

    def run(self):
        pass
