from ulauncher.utils.singleton import Singleton


def test_class_singleton() -> None:
    class TestClass(metaclass=Singleton):
        def __init__(self) -> None:
            pass

    assert TestClass() == TestClass()
