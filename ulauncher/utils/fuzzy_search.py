from functools import lru_cache
from Levenshtein import matching_blocks, editops


@lru_cache(maxsize=1000)
def get_matching_blocks(query, text):
    """
    Uses Levenstein library's get_matching_blocks (Longest Common Substring),
    This is 8-12x faster than difflib's SequenceMatcher().get_matching_blocks()
    :returns: list of tuples, containing the index and matching block, number of characters that matched
    """
    query_l = query.lower()
    text_l = text.lower()
    blocks = matching_blocks(editops(query_l, text_l), query_l, text_l)[:-1]
    output = []
    total_len = 0
    for (_, text_index, length) in blocks:
        output.append((text_index, text[text_index: text_index + length]))
        total_len += length
    return output, total_len


def get_score(query, text):
    """
    Uses get_matching_blocks() to figure out how much of the query that matches the text,
    and tries to weight this to slightly favor shorter results and largely favor word matches
    :returns: number between 0 and 100
    """

    if not query or not text:
        return 0

    query_len = len(query)
    text_len = len(text)
    max_len = max(query_len, text_len)
    blocks, matching_chars = get_matching_blocks(query, text)

    # Ratio of the query that matches the text
    base_similarity = matching_chars / query_len

    # Lower the score if the match is in the middle of a word.
    for index, _ in blocks:
        is_word_boundary = index == 0 or text[index - 1] == ' '
        if not is_word_boundary:
            base_similarity -= 0.5 / query_len

    # Rank matches lower for each extra character, to slightly favor shorter ones.
    score = 100 * base_similarity * query_len / (query_len + (max_len - query_len) * 0.001)

    return score
