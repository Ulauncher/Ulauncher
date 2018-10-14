# -*- coding: utf-8 -*-

from ulauncher.util.compat import map_

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
                  otherwise returns ``any(map_(lambda i: i.keep_app_open(), self))``
        """
        if not self:
            return True
        else:
            return any(map_(lambda i: i.keep_app_open(), self))

    def run(self):
        map_(lambda i: i.run(), self)
