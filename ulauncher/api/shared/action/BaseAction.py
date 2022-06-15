class BaseAction:
    keep_app_open = False

    def run(self):
        """
        Runs action
        """
        raise RuntimeError(f"{self.__class__.__name__}#run() is not implemented")
