from .BaseAction import BaseAction


class SetUserQueryAction(BaseAction):

    def __init__(self, new_query):
        self.new_query = new_query

    def keep_app_open(self):
        return True

    def run(self):
        from ulauncher.ui.windows.UlauncherWindow import UlauncherWindow
        UlauncherWindow.get_instance().input.set_text(self.new_query)
