import math
from gi.repository import GLib


class TimerContext:
    """A utility class to hold the context for the timer() function."""

    def __init__(self, source, func, repeat=False):
        self.source = source
        self.repeat = repeat
        self.func = func
        self.source.set_callback(self.trigger)
        self.source.attach(None)

    def cancel(self):
        if self.source:
            self.source.destroy()
            self.source = None

    # pylint: disable=unused-argument
    def trigger(self, user_data):
        self.func()
        return self.repeat


def timer(delay_sec, func, repeat=False):
    """
    Executes the given function after a delay given in seconds. Repeats every delay_sec if
    repeat==True. The function is executed in the context of the GLib MainContext thread.

    func is not called with any arguments, so to call with custom arguments use functools.partial,
    such as `timer(0.5, partial(myfunc, myarg1, myarg2))`.

    To cancel the timer, call `.cancel()` on the returned object.

    """
    frac, _ = math.modf(delay_sec)
    if frac == 0.0:
        source = GLib.timeout_source_new_seconds(delay_sec)
    else:
        source = GLib.timeout_source_new(delay_sec * 1000)

    return TimerContext(source, func, repeat)
