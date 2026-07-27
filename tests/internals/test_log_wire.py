import logging

from ulauncher.internals import log_wire


def _wire(name: str, message: str) -> str:
    record = logging.LogRecord(name, logging.WARNING, "/ext/main.py", 12, message, None, None, func="run")
    return log_wire.WireFormatter().format(record)


def test_round_trip__preserves_the_record() -> None:
    message = 'Traceback (most recent call last):\n  File "main.py"\nValueError: back\\slash'
    line = _wire("__main__", message)

    assert "\n" not in line
    parsed = log_wire.parse(line)
    assert parsed
    assert (parsed.levelno, parsed.pathname, parsed.lineno, parsed.funcName) == (
        logging.WARNING,
        "/ext/main.py",
        12,
        "run",
    )
    assert parsed.getMessage() == message
    assert parsed.name == "__main__"


def test_parse__plain_output__is_not_a_record() -> None:
    assert log_wire.parse("just a print") is None
    assert log_wire.parse('{"name": "my.ext"}') is None
