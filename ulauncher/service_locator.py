objects = {}


def singleton(fn):
    """
    Decorator function.
    Call to a decorated function always returns the same instance
    Note: it doesn't take into account args and kwargs when looks up a saved instance
    Call a decorated function with spawn=True in order to get a new instance
    """
    def wrapper(spawn=False):
        if not spawn and objects.get(fn):
            return objects[fn]
        else:
            instance = fn()
            objects[fn] = instance
            return instance

    return wrapper


@singleton
def getUlauncherWindow():
    from .UlauncherWindow import UlauncherWindow
    return UlauncherWindow()


@singleton
def getIndicator():
    from .Indicator import Indicator
    return Indicator.create("ulauncher", getUlauncherWindow())


@singleton
def getSettings():
    from ulauncher_lib.ulauncherconfig import SETTINGS_FILE_PATH
    from ulauncher_lib.Settings import Settings
    return Settings.new_from_file(SETTINGS_FILE_PATH)
