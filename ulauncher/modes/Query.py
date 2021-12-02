class Query(str):
    """
    Parses user's query
    """

    def get_keyword(self):
        return self and self.split(None, 1)[0]

    def get_argument(self, default=None):
        return self and (self.split(None, 1) + [default])[1]
