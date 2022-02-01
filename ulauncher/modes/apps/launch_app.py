import logging
import re
import shlex
import gi

gi.require_version("Gio", "2.0")
# pylint: disable=wrong-import-position
from gi.repository import Gio
from ulauncher.utils.Settings import Settings
from ulauncher.utils.launch_detached import launch_detached

logger = logging.getLogger(__name__)
settings = Settings.get_instance()


def launch_app(app_id):
    app = Gio.DesktopAppInfo.new(app_id)
    app_exec = app.get_commandline()
    if app.get_boolean('DBusActivatable'):
        # https://wiki.gnome.org/HowDoI/DBusApplicationLaunching
        exec = ['gapplication', 'launch', app_id.replace('.desktop', '')]
    elif app_exec:
        # strip field codes %f, %F, %u, %U, etc
        stripped_app_exec = re.sub(r'\%[uUfFdDnNickvm]', '', app_exec).rstrip()
        if app.get_boolean('Terminal'):
            terminal_exec = settings.get_property('terminal-command')
            if terminal_exec:
                logger.info('Will run command in preferred terminal (%s)', terminal_exec)
                exec = shlex.split(terminal_exec) + [stripped_app_exec]
            else:
                exec = ['gtk-launch', app_id]
        else:
            exec = shlex.split(stripped_app_exec)

    if not exec:
        logger.error("No command to run %s", app_id)
    else:
        logger.info('Run application %s (%s) Exec %s', app.get_name(), app_id, exec)
        launch_detached(exec)
