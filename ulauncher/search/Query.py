class Query(unicode):
    """
    Parses user's query
    """

    def get_keyword(self):
        return self.strip().split(' ', 1)[0]

    def is_mode_active(self):
        """
        Mode is active when query starts with keyword + space
        """
        kw = self.get_keyword()
        return kw and self.startswith('%s ' % kw)

    def get_argument(self, default=None):
        try:
            return self.strip().split(' ', 1)[1].strip()
        except IndexError:
            return default
