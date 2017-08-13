from ulauncher.util.SortedCollection import SortedCollection
from ulauncher.util.fuzzy_search import get_score


class SortedList(object):
    """
    List maintains result items in a sorted order
    (sorted by a score, which is a similarity between item's name and a query)
    and limited to a number `limit` passed into the constructor
    """

    def __init__(self, query, min_score=30, limit=9):
        self._query = query.lower().strip()
        self._min_score = min_score
        self._limit = limit
        self._items = SortedCollection(key=lambda i: i.score)

    def __len__(self):
        return len(self._items)

    def __getitem__(self, i):
        return self._items[i]

    def __iter__(self):
        return iter(self._items)

    def __reversed__(self):
        return reversed(self._items)

    def __repr__(self):
        return '%s(%r, min_score=%s, limit=%s)' % (
            self.__class__.__name__,
            self._items,
            self._min_score,
            self._limit
        )

    def __contains__(self, item):
        return item in self._items

    def extend(self, items):
        map(lambda i: self.append(i), items)

    def append(self, result_item):
        score = get_score(self._query, result_item.get_search_name())
        if score >= self._min_score:
            result_item.score = -score  # use negative to sort by score in desc. order
            self._items.insert(result_item)
            while len(self._items) > self._limit:
                self._items.pop()  # remove items with the lowest score to maintain limited number of items
