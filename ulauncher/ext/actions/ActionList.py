class ActionList(list):

    def keep_app_open(self):
        return any(map(lambda i: i.keep_app_open(), self))

    def run_all(self):
        map(lambda i: i.run(), self)
