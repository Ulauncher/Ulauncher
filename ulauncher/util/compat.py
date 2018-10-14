# -*- coding: utf-8 -*-

#   from ulauncher.util.compat import print_stderr

import sys

# PY3 is left as bw-compat but PY2 should be used for most checks.
PY2 = sys.version_info[0] == 2
PY3 = sys.version_info[0] == 3

if PY2:
   # string_types = basestring,  # noqa
   # integer_types = (int, long)  # noqa
   # class_types = (type, types.ClassType)  # noqa
    text_type = unicode  # noqa
   # binary_type = str  # noqa
   # long = long  # noqa
else:
    # string_types = str,
    # integer_types = int,
    # class_types = type,
    text_type = str
    # binary_type = bytes
    # long = int

if PY2:
    from urllib import unquote
    from urllib import urlretrieve
    from urllib2 import urlopen
else:
    from urllib.parse import unquote  # noqa
    from urllib.request import urlretrieve  # noqa
    from urllib.request import urlopen  # noqa

if PY2:  # pragma: no cover
    def iteritems_(d):
        return d.iteritems()

    def itervalues_(d):
        return d.itervalues()

    # def iterkeys_(d):
    #     return d.iterkeys()

else:  # pragma: no cover
    def iteritems_(d):
        return d.items()

    def itervalues_(d):
        return d.values()

    # def iterkeys_(d):
    #     return d.keys()

if PY2:
    map_ = map
else:
    def map_(*arg):
        return list(map(*arg))

if PY2:
    from BaseHTTPServer import BaseHTTPRequestHandler
else:
    from http.server import BaseHTTPRequestHandler  # noqa

if PY2:
    from io import BytesIO as NativeIO
else:
    from io import StringIO as NativeIO  # noqa

if PY2:
    def byte2int(datum):
        return ord(datum)
else:
    def byte2int(datum):
        return datum
