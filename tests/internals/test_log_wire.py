import logging

from ulauncher.internals import log_wire


def _wire(**overrides: object) -> str:
    fields: dict[str, object] = {
        "name": "my.ext",
        "level": logging.WARNING,
        "pathname": "/ext/main.py",
        "lineno": 12,
        "msg": "hello",
        "args": None,
        "exc_info": None,
        "func": "run",
    }
    fields.update(overrides)
    return log_wire.WireFormatter().format(logging.LogRecord(**fields))  # type: ignore[arg-type]


def test_round_trip__preserves_the_record() -> None:
    parsed = log_wire.parse(_wire(name="__main__"), "my.ext")

    assert parsed
    assert (parsed.levelno, parsed.pathname, parsed.lineno, parsed.funcName) == (
        logging.WARNING,
        "/ext/main.py",
        12,
        "run",
    )
    assert parsed.getMessage() == "hello"
    assert parsed.name == "my.ext.__main__"  # the extension's own logger name keeps its id as-is
    assert log_wire.parse(_wire(), "my.ext").name == "my.ext"  # type: ignore[union-attr]


def test_round_trip__multiline_message__stays_one_line_on_the_wire() -> None:
    message = 'Traceback (most recent call last):\n  File "main.py"\nValueError: back\\slash'
    line = _wire(msg=message)

    assert "\n" not in line
    parsed = log_wire.parse(line, "my.ext")
    assert parsed
    assert parsed.getMessage() == message


def test_parse__plain_output__is_not_a_record() -> None:
    assert log_wire.parse("just a print", "my.ext") is None
    assert log_wire.parse("WARNING\x1fmy.ext\x1f/ext/main.py\x1f12\x1frun\x1fhello", "my.ext") is None
