from ulauncher.api.shared.event import BaseEvent


class SampleEvent1(BaseEvent):
    prop1 = "string"
    prop2 = 12

    def __init__(self, arg1):
        self.arg1 = arg1


class SampleEvent2(BaseEvent):
    prop1 = "string"
    prop2 = 12

    def __init__(self, arg1):
        self.arg1 = arg1


class TestBaseEvent:
    def test_eq__objects_of_the_same_class__are_equal(self):
        assert SampleEvent1("test") == SampleEvent1("test")

    def test_ineq__objects_of_the_same_class__are_equal(self):
        assert SampleEvent1("test") == SampleEvent1("test")

    def test_eq__objects_of_different_classes__are_not_equal(self):
        assert SampleEvent1("test") != SampleEvent2("test")
