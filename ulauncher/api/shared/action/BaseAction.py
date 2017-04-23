class BaseAction(object):

    def keep_app_open(self):
        """
        :rtype: bool
        :returns: True if Ulauncher window should remain open once all actions are done
        """
        return False

    def run(self):
        """
        Runs action
        """
        raise RuntimeError("%s#run() is not implemented" % self.__class__.__name__)
