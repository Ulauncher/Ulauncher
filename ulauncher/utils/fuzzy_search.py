from functools import lru_cache
from Levenshtein import distance, matching_blocks, editops


@lru_cache(maxsize=150)
def get_matching_blocks(query, text):
    """
    Uses Levenstein library's get_matching_blocks (Longest Common Substring),
    This is 8-12x faster than difflib's SequenceMatcher().get_matching_blocks()
    :returns: List of tuples, containing the index and matching block
    """
    query_l = query.lower()
    text_l = text.lower()
    blocks = matching_blocks(editops(query_l, text_l), query_l, text_l)[:-1]
    output = []
    for (_, text_index, length) in blocks:
        output.append((text_index, text[text_index: text_index + length]))
    return output


def get_score(query, text):
    """
    Uses Levenshtein's algorithm + some improvements to the score
    :returns: number between 0 and 100
    """
    query = query.lower()
    text = text.lower()
    query_len = len(query)
    if not query or not text:
        return 0

    # Wrap and counter-weight distance so that short queries can match better with long texts.
    # With regular levensteins distance "Fir" and "Firefox" is only 3/7 similar
    # This is counter-weighted by 95% here, so it still has a slight benefit when your query matches a short app name.
    diff = distance(query, text) - (max(0, len(text) - query_len) * .95)
    score = 100 * max(0, query_len - diff) / query_len

    # Raise the score by 30% if the query fully matches the beginning of a word
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
