from ulauncher.api.shared.action.BaseAction import BaseAction


class ActionList(list, BaseAction):
    """
    Used to run multiple action at once

    :param list actions: list of actions to run
    """

    @property
    def keep_app_open(self):
        """
        :rtype: boolean
        :returns: return true any action should keep the window open or if the list is empty
        """
        if not self:
            return True

        for item in self:
            if item is True or isinstance(item, (str, list)) or (isinstance(item, BaseAction) and item.keep_app_open):
                return True

        return False

    def run(self):
        for item in self:
            item.run()
