import logging

from ulauncher.internals import log_wire


def _wire(name: str, message: str) -> str:
    record = logging.LogRecord(name, logging.WARNING, "/ext/main.py", 12, message, None, None, func="run")
    return log_wire.WireFormatter().format(record)


def test_round_trip__preserves_the_record() -> None:
    message = 'Traceback (most recent call last):\n  File "main.py"\nValueError: back\\slash'
    line = _wire("__main__", message)

    assert "\n" not in line
    parsed = log_wire.parse(line, "my.ext")
    assert parsed
    assert (parsed.levelno, parsed.pathname, parsed.lineno, parsed.funcName) == (
        logging.WARNING,
        "/ext/main.py",
        12,
        "run",
    )
    assert parsed.getMessage() == message
    assert parsed.name == "my.ext.__main__"


def test_round_trip__extensions_own_logger__keeps_its_name() -> None:
    parsed = log_wire.parse(_wire("my.ext", "hello"), "my.ext")

    assert parsed
    assert parsed.name == "my.ext"


def test_parse__plain_output__is_not_a_record() -> None:
    assert log_wire.parse("just a print", "my.ext") is None
    assert log_wire.parse('{"name": "my.ext"}', "my.ext") is None
