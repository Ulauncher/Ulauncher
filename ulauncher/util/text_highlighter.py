from ulauncher.util.fuzzy_search import get_matching_indexes
from ulauncher.util.string import force_unicode


def highlight_text(query, text, open_tag='<span foreground="white">', close_tag='</span>'):
    """
    Highlights words from query in a given text string
    :returns: string with Pango markup
    """
    positions = get_matching_indexes(query, text)
    query = force_unicode(query)
    text = force_unicode(text)

    # use positions to highlight text with tags
    hl_started = False
    hlted = []
    for i, char in enumerate(text):
        if i in positions and not hl_started:
            hl_started = True
            hlted.append(open_tag)
        elif i not in positions and hl_started:
            hl_started = False
            hlted.append(close_tag)

        hlted.append(char)

    if hl_started:
        # don't forget to close tag if it is opened
        hlted.append(close_tag)

    # replace & characters with &amp;
    return ''.join(hlted).replace('&', '&amp;')
