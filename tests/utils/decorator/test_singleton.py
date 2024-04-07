from ulauncher.utils.decorator.singleton import class_singleton


def test_class_singleton():
    @class_singleton
    class TestClass:
        def __init__(self) -> None:
            pass

    assert TestClass() == TestClass()
