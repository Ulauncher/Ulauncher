from .BaseAction import BaseAction


class KeepAppOpenAction(BaseAction):

    def keep_app_open(self):
        return True

    def run(self):
        pass
