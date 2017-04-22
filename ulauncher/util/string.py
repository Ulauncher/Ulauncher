import re

_first_cap_re = re.compile('(.)([A-Z][a-z]+)')
_all_cap_re = re.compile('([a-z0-9])([A-Z])')


def force_unicode(text):
    return text if isinstance(text, unicode) else text.decode('utf8')


def split_camel_case(text, sep='_'):
    s1 = _first_cap_re.sub(r'\1%s\2' % sep, text)
    return _all_cap_re.sub(r'\1%s\2' % sep, s1).lower()
