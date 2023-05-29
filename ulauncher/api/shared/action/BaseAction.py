class BaseAction:
    keep_app_open = False

    def run(self):
        """
        Runs action
        """
        msg = f"{self.__class__.__name__}#run() is not implemented"
        raise RuntimeError(msg)
