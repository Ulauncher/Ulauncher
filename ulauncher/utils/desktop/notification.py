import gi
try:
    gi.require_version("Notify", "0.7")
except ValueError:
    gi.require_version("Notify", "0.8")

# pylint: disable=wrong-import-position
# type: ignore
from gi.repository import Notify

Notify.init('ulauncher')


def show_notification(summary, body, icon='ulauncher'):
    """
    :rtype: :class:`Notify.Notification`
    """
    Notify.Notification.new(summary, body, icon).show()
