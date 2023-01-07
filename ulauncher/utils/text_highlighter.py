from ulauncher.utils.fuzzy_search import get_matching_blocks


def highlight_text(query, text: str, open_tag='<span foreground="white">', close_tag="</span>") -> str:
    """
    Highlights words from query in a given text string
    :returns: string with Pango markup
    """
    text = text.replace("&amp;", "&")

    # Traverse through blocks in reverse order so we don't change the text index for the next iteration
    for index, chars in reversed(get_matching_blocks(query, text)[0]):
        text = text[0:index] + open_tag + chars + close_tag + text[index + len(chars) :]

    return text.replace("&", "&amp;")
