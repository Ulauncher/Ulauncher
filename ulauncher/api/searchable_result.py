from ulauncher.utils.fuzzy_search import get_score
from ulauncher.api.result import Result


class SearchableResult(Result):
    searchable = True
    highlightable = True

    def get_searchable_fields(self):
        return [(self.name, 1), (self.description, .8)]

    def search_score(self, query):
        return max(get_score(query, field) * weight for field, weight in self.get_searchable_fields() if field)
