from __future__ import annotations

from typing import Generator

from ulauncher.utils.fuzzy_search import get_matching_blocks


def highlight_text(query, text: str) -> Generator[tuple[str, bool], None, None]:
    block_index = 0
    for index, chars in get_matching_blocks(query, text)[0]:
        chars_len = len(chars)
        if index != block_index:
            yield (text[block_index:index], False)
        yield (chars, True)
        block_index = index + chars_len
    if block_index < len(text):
        yield (text[block_index:], False)
