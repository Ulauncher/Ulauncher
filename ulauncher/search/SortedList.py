from ulauncher.util.SortedCollection import SortedCollection
from ulauncher.util.fuzzy_search import get_score


class SortedList(object):
    """
    List maintains result items in a sorted order
    (sorted by a score, which is a similarity between item's name and a query)
    and limited to a number `limit` passed into the constructor
    """

    def __init__(self, query, min_score=30, limit=9):
        print ""
        print ""
        print "=> => => =>"
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
        search_name = result_item.get_search_name()

        score = 0
        words = search_name.split(' ')
        matchy_word_count = 0
        full_already_word_found = False

        for word in words:
            # if found a full word, score VERY high, but only do so once
            # to avoid repetative word scenario
            if self._query == word:
                if full_already_word_found is False:
                    score += 100000
                    matchy_word_count += 1
                    full_already_word_found = True
                else:
                    continue
            # if found a partial, give it a nice boost
            elif self._query in word:
                score += 1000
                matchy_word_count += 1
            else:
                word_score = int(round(get_score(self._query, word), 0))
                if word_score > self._min_score:
                    score += word_score
                    matchy_word_count += 1

        # get a ration of score to words found. this helps mitigate the
        # situation where some application have a lot of keywords and long
        # descriptions and get ranked higher
        if matchy_word_count > 0:
            matchy_score = score / matchy_word_count
        else:
            matchy_score = 0

        print matchy_score, matchy_word_count, score, len(words), search_name

        if matchy_word_count > 0:
            # use negative to sort by score in desc. order
            result_item.score = -matchy_score
            self._items.insert(result_item)
            # remove items with the lowest score to maintain limited number of
            # items
            while len(self._items) > self._limit:
                self._items.pop()
