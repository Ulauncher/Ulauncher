from .BaseAction import BaseAction


class DoNothingAction(BaseAction):

    def keep_app_open(self):
        return True

    def run(self):
        pass
