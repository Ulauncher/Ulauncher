"""
Simple module to call XInitThreads() to properly support multi-threaded X11 applications.
"""
from ctypes import cdll

# Using libX11.so.6 may seem a bit hard-coded, but a quick search on the Internet indicates
# discussion of this ABI version back to before 2009, 12 years prior to when this code was added.
# Also, with most of the development focus on Wayland, the chance of a ABI version bump in X11 is
# exceptionally small. Therefore, no additional fancy discovery methods are necessary.
x11 = cdll.LoadLibrary("libX11.so.6")
x11.XInitThreads()
