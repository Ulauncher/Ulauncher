from .BaseAction import BaseAction


class RenderResultListAction(BaseAction):

    def __init__(self, restul_list):
        """
        :param list restul_list: list of ResultItem objects
        """
        self.restul_list = restul_list

    def keep_app_open(self):
        return True

    def run(self):
        from ulauncher.ui.windows.UlauncherWindow import UlauncherWindow
        UlauncherWindow.get_instance().show_results(self.restul_list)
