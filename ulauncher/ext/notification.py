from gi.repository import Notify

Notify.init('ulauncher')


def show_notification(summary, body, icon='ulauncher'):
    """
    Returns Notification
    """
    Notify.Notification.new(summary, body, icon).show()
