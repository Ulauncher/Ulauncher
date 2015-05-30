class BaseAction(object):

    def keep_app_open(self):
        return False

    def run(self):
        raise RuntimeError("%s#run() is not implemented" % self.__class__.__name__)
