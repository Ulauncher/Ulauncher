class ActionList(list):

    def keep_app_open(self):
        """
        Retruns True if ulauncher window should remain open once all actions are done
        """
        # return true if there no actions in the list
        if not self:
            return True
        else:
            return any(map(lambda i: i.keep_app_open(), self))

    def run_all(self):
        map(lambda i: i.run(), self)
