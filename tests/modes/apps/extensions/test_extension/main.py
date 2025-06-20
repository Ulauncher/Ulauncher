import signal
import sys
from time import sleep


def exit_gracefully(_signum, _frame) -> None:
    print("On SIGTERM")
    sleep(3)


signal.signal(signal.SIGTERM, exit_gracefully)

while True:
    print("stdout check", file=sys.stdout)
    sleep(2)
    print("stderr check", file=sys.stderr)

sys.exit(0)
