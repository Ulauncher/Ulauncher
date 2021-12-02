class Query(str):
    """
    Parses user's query
    """

    def get_keyword(self):
        return self.strip().split(' ', 1)[0]

    def get_argument(self, default=None):
        try:
            return self.strip().split(' ', 1)[1].strip()
        except IndexError:
            return default
