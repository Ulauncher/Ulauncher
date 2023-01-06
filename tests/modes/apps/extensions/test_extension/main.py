import sys
from time import sleep
import signal


# pylint: disable=unused-argument
def exit_gracefully(signum, frame):
    print("On SIGTERM")
    sleep(3)


signal.signal(signal.SIGTERM, exit_gracefully)

while True:
    print("stdout check", file=sys.stdout)
    sleep(2)
    print("stderr check", file=sys.stderr)

sys.exit(0)
