from ulauncher.utils.fuzzy_search import get_score
from .result import Result


class SearchableResult(Result):
    searchable = True

    def search_score(self, query):
        return get_score(query, self.get_name())
