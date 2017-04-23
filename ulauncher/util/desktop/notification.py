from gi.repository import Notify

Notify.init('ulauncher')


def show_notification(summary, body, icon='ulauncher'):
    """
    :rtype: :class:`Notify.Notification`
    """
    Notify.Notification.new(summary, body, icon).show()
