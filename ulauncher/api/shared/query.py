class Query(str):
    # Splits to a list with the keyword and argument and pad with empty strings
    def _get_components(self):
        components = self.split(None, 1)
        return components + [""] * (2 - len(components))

    @property
    def keyword(self):
        return self._get_components()[0]

    @property
    def argument(self):
        return self._get_components()[1]

    def get_keyword(self):
        return self.keyword

    def get_argument(self, default=None):
        return self.argument or default
