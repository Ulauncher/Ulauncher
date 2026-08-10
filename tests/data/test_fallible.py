from ulauncher.data import Err, Fallible, Ok


def half_of_even(number: int) -> Fallible[int, str]:
    if number % 2:
        return Err(f"{number} is odd")
    return Ok(number // 2)


class TestFallible:
    def test_narrowing_reaches_the_value(self) -> None:
        result = half_of_even(4)
        assert not isinstance(result, Err)
        assert result.value == 2

    def test_narrowing_reaches_the_error(self) -> None:
        result = half_of_even(3)
        assert isinstance(result, Err)
        assert result.error == "3 is odd"

    def test_equality(self) -> None:
        assert Ok(1) == Ok(1)
        assert Ok(1) != Ok(2)
        assert Err("x") == Err("x")
        assert Ok(1) != Err(1)

    def test_repr(self) -> None:
        assert repr(Ok(1)) == "Ok(1)"
        assert repr(Err("x")) == "Err('x')"
