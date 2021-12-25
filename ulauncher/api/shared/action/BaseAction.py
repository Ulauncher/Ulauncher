class BaseAction:

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
        raise RuntimeError(f"{self.__class__.__name__}#run() is not implemented")
