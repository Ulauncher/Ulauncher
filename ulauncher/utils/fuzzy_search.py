from __future__ import annotations

import unicodedata
from difflib import SequenceMatcher
from typing import NamedTuple

from ulauncher.utils.lru_cache import lru_cache


# characters that should be stripped during normalization:
# "Mn" = combining marks (accents/diacritics), non-ASCII punctuation (e.g. curly quotes)
def _is_stripped(char: str) -> bool:
    cat = unicodedata.category(char)
    return cat == "Mn" or (cat[0] == "P" and not char.isascii())


# casefold, decompose (NFD) and strip, so ex "motörhead" matches "Motorhead"
def _normalize_char(char: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", char.casefold()) if not _is_stripped(c))


@lru_cache(maxsize=2000)
def _normalize(string: str) -> str:
    # per char, so _normalize_with_map can reuse the same normalization
    return "".join(map(_normalize_char, string))


class _NormalizedText(NamedTuple):
    """Normalized text with a map from each normalized char back to its original char index."""

    text: str
    orig_indexes: list[int]

    def orig_span(self, index: int, length: int) -> tuple[int, int]:
        """Map a span in normalized text to its (start, end) span in the original text."""
        # no map entry past the last kept char, hence last char index + 1
        return self.orig_indexes[index], self.orig_indexes[index + length - 1] + 1


@lru_cache(maxsize=10000)
def _normalize_with_map(text: str) -> _NormalizedText:
    chars: list[str] = []
    orig_indexes: list[int] = []
    for orig_idx, char in enumerate(text):
        normalized = _normalize_char(char)
        # a char may expand (ß -> ss) or be dropped (stripped marks)
        orig_indexes.extend([orig_idx] * len(normalized))
        chars.append(normalized)
    return _NormalizedText("".join(chars), orig_indexes)


@lru_cache(maxsize=20000)
def get_matching_blocks(query_str: str, text: str) -> tuple[list[tuple[int, str]], int]:
    """
    Find the blocks using "Longest Common Substrings",
    :returns: list of tuples, containing the index and matching block sliced from `text`,
              number of characters that matched
    """
    norm_text = _normalize_with_map(text)
    blocks = SequenceMatcher(None, _normalize(query_str), norm_text.text).get_matching_blocks()[:-1]
    spans: list[tuple[int, int]] = []
    total_len = 0
    for _, text_index, length in blocks:
        start, end = norm_text.orig_span(text_index, length)
        total_len += length
        # chars expanded by normalization (ß -> ss) can be matched by separate blocks,
        # so the translated spans may overlap and need to be merged
        if spans and start < spans[-1][1]:
            spans[-1] = (spans[-1][0], end)
        else:
            spans.append((start, end))
    return [(start, text[start:end]) for start, end in spans], total_len


def get_score(query_str: str, text: str) -> float:
    """
    Uses get_matching_blocks() to figure out how much of the query that matches the text,
    and tries to weight this to slightly favor shorter results and largely favor word matches
    :returns: number between 0 and 100
    """

    if not query_str or not text:
        return 0.0

    query_len = len(query_str)
    text_len = len(text)
    max_len = max(query_len, text_len)
    blocks, matching_chars = get_matching_blocks(query_str, text)

    # Ratio of the query that matches the text
    base_similarity = matching_chars / query_len

    # Lower the score if the match is in the middle of a word.
    for index, _ in blocks:
        is_word_boundary = index == 0 or text[index - 1] == " "
        if not is_word_boundary:
            base_similarity -= 0.5 / query_len

    # Rank matches lower for each extra character, to slightly favor shorter ones.
    return 100 * base_similarity * query_len / (query_len + (max_len - query_len) * 0.001)
