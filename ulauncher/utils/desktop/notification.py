import logging
import gi

try:
    gi.require_version("Notify", "0.7")
except ValueError:
    gi.require_version("Notify", "0.8")

# pylint: disable=wrong-import-position
from gi.repository import Notify  # type: ignore[attr-defined]

Notify.init("ulauncher")
logger = logging.getLogger()


def show_notification(summary, body, icon="ulauncher"):
    """
    :rtype: :class:`Notify.Notification`
    """
    try:
        Notify.Notification.new(summary, body, icon).show()
    except Exception as e:
        logger.exception("Unexpected notification error. %s: %s", type(e).__name__, e)
