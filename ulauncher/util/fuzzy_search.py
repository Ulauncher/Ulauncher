from __future__ import division
import operator
from Levenshtein import ratio
from ulauncher.util.string import force_unicode
from ulauncher.util.decorator.lru_cache import lru_cache


@lru_cache(maxsize=150)
def get_matching_indexes(query, text):
    """
    Uses Longest Common Substring Algorithm to find the best match

    Runs in O(nm)

    :returns: a list of positions of chars from query inside text
    """
    query = query.lower()
    text = text.lower()
    m = len(query)
    n = len(text)
    counter = [[0] * (n + 1) for x in range(m + 1)]
    for i in range(m):
        for j in range(n):
            if query[i] == text[j]:
                c = counter[i][j] + 1
                counter[i + 1][j + 1] = c

    #       F  i  r  e  f  o  x     W  e  b     B  r  o  w  s  e  r
    #  [[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    # f [0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    # i [0, 0, 2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    # w [0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0],
    # e [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 2, 0, 0, 0, 0, 0, 0, 0, 1, 0],
    # b [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 3, 0, 1, 0, 0, 0, 0, 0, 0],
    # r [0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 2, 0, 0, 0, 0, 1],
    # o [0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 3, 0, 0, 0, 0]]

    positions = set()
    i = m
    while i > 0:
        j, c = max(enumerate(counter[i]), key=operator.itemgetter(1))
        if c:
            map(positions.add, range(j - c, j))
            i -= c
        else:
            i -= 1

    return sorted(positions)


def get_score(query, text):
    """
    Uses Levenshtein's algorithm + some improvements to the score
    :returns: number between 0 and 100
    """
    if not query or not text:
        return 0

    query = query.lower()
    text = text.lower()
    score = ratio(force_unicode(query), force_unicode(text)) * 100

    # increase score if a word from text starts with a query
    for text_part in text.split(' '):
        if text_part.startswith(query):
            score += 30
            break

    # increase score if each separate group in indexes is a beginning of a word in text
    # example for query 'fiwebr' groups 'fi', 'we', and 'br' are matching word beginnings
    # of text 'Firefox Web Browser'
    # increase score for each such group
    increment = 10
    i = 0  # query iterator
    lq = len(query)
    for j, char in enumerate(text):
        # run until query ends and check if a query char. equals to current text char
        if i < lq and query[i] == char:
            # if char from query matches beginning of text or beginning of a word inside the text, increase the score
            if j == 0 or text[j - 1] in ' .(-_+)':
                score += increment
            i += 1
        elif i == lq:
            break

    return min(100, score)
