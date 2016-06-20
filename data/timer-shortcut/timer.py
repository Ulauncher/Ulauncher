#!/usr/bin/env python

import sys
import re
import subprocess
from time import sleep
from gi.repository import Notify


Notify.init("timer-shortcut")
sound = True
timeSec = 0
iconPath = "{ICON_PATH}"
soundCmd = ("paplay", "/usr/share/sounds/freedesktop/stereo/complete.oga")
timeMult = {
    'h': 60 * 60,
    'm': 60,
    's': 1
}

try:
    subject = sys.argv[2]
except IndexError:
    subject = 'Time is up!'

try:
    timeArg = sys.argv[1]
except IndexError:
    subject = "*You didn't specify time*"
    sound = False
else:
    try:
        m = re.match(r'^(?P<time>\d+)(?P<measure>[mhs])?$', timeArg, re.I)
        timeSec = int(m.group('time')) * timeMult[(m.group('measure') or 's').lower()]
    except Exception as e:
        print(e)
        subject = '*Invalid time "%s"*' % timeArg

if timeSec:
    Notify.Notification.new("Timer", "Counting down %s to '%s'..." % (timeArg, subject), iconPath).show()

sleep(timeSec)
Notify.Notification.new("Timer", subject, iconPath).show()
subprocess.call(soundCmd)
