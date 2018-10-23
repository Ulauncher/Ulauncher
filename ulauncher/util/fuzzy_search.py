from fuzzywuzzy import fuzz
from ulauncher.util.decorator.lru_cache import lru_cache


@lru_cache(maxsize=150)
def get_matching_indexes(query, text):
    """
    Uses Longest Common Substring Algorithm to find the best match

    Runs in O(nm)

    :returns: a list of positions of chars from query inside text
    """
    seq_match = fuzz.SequenceMatcher(seq1=query.lower(), seq2=text.lower())

    positions = []
    for (operation, _, _, text_start, text_end) in seq_match.get_opcodes():
        if operation == 'equal':
            positions += range(text_start, text_end)

    return sorted(positions)
