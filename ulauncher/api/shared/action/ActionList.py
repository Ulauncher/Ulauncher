from .BaseAction import BaseAction


class ActionList(list, BaseAction):
    """
    Used to run multiple action at once

    :param list actions: list of actions to run
    """

    def keep_app_open(self):
        """
        :rtype: boolean
        :returns: return true if there are no actions in the list
                  otherwise returns ``any(map(lambda i: i.keep_app_open(), self))``
        """
        if not self:
            return True
        else:
            return any(map(lambda i: i.keep_app_open(), self))

    def run(self):
        map(lambda i: i.run(), self)
