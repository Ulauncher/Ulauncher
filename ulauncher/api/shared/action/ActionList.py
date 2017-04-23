from .BaseAction import BaseAction


class ActionList(list, BaseAction):

    def keep_app_open(self):
        """
        :rtype: bool
        :returns: True if Ulauncher window should remain open once all actions are done
        """

        # return true if there no actions in the list
        if not self:
            return True
        else:
            return any(map(lambda i: i.keep_app_open(), self))

    def run(self):
        map(lambda i: i.run(), self)
