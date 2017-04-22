from .BaseAction import BaseAction


class CloseAppAction(BaseAction):

    def keep_app_open(self):
        return False

    def run(self):
        pass
