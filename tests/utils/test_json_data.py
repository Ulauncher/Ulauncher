import json
import shutil
import pytest
from ulauncher.utils.json_data import JsonData, json_data_class

json_file = "/tmp/ulauncher-test/jsondata.json"


def teardown_module(module):
    shutil.rmtree("/tmp/ulauncher-test")


def load_json(file=json_file):
    try:
        with open(file) as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


class TestJsonData:
    def test_attr_methods(self):
        jd = JsonData()
        assert not hasattr(jd, "a")
        with pytest.raises(AttributeError):
            jd.a
        jd.a = False
        assert hasattr(jd, "a")
        assert jd.a is False

    def test_setting_and_comparison(self):
        jd = JsonData()
        jd.a = 1
        jd.update({"b": 2}, c=3)
        jd["d"] = 4
        assert jd == JsonData(a=1, b=2, c=3, d=4)
        assert JsonData(b=2, a=1) == JsonData({"a": 1, "b": 2})
        assert JsonData(a=1, b=2) != JsonData({"a": 1})

    def test_new_file_file_cache(self):
        file_path = "/tmp/ulauncher-test/jsondata_test_cache.json"
        jd1 = JsonData.new_from_file(file_path)
        assert not hasattr(jd1, "a")
        jd1.a = 1
        jd2 = JsonData.new_from_file(file_path)
        assert id(jd2) == id(jd1)  # tests that it's actually the same object in memory
        assert jd2.a == 1

    def test_stringify(self):
        assert JsonData(a=1, c=3, b=2).stringify() == '{"a": 1, "b": 2, "c": 3}'
        assert JsonData(a=1, c=3, b=2).stringify(sort_keys=False) == '{"a": 1, "c": 3, "b": 2}'
        assert JsonData(a=1, b=2).stringify(indent=4) == '{\n    "a": 1,\n    "b": 2\n}'
        assert JsonData(a=None, b=[], c={}, d=1).stringify() == '{"d": 1}'

        class UnfilteredJSONData(JsonData):
            __json_value_blacklist__ = []

        assert UnfilteredJSONData(a=None, b=[], c={}).stringify() == '{"a": null, "b": [], "c": {}}'

    def test_save_as(self):
        # Check that JsonData initiated w or w/o path saves to the path specified,
        # not the instance path
        file_path = "/tmp/ulauncher-test/jsondata_save_as.json"
        jd_static = JsonData(abc=123)
        jd_static.save_as(file_path)
        assert load_json(file_path).get("abc") == 123
        jd = JsonData.new_from_file(json_file)
        jd.save()
        jd.bcd = 234
        jd.save_as(file_path)
        assert load_json().get("abc", None) is None
        assert load_json(file_path).get("abc") is None
        assert load_json(file_path).get("bcd") == 234

    def test_save(self):
        jd = JsonData.new_from_file(json_file)
        jd.asdf = "xyz"
        jd.save()
        assert load_json().get("asdf") == "xyz"
        jd.save(asdf="zyx")
        assert load_json().get("asdf") == "zyx"

    def test_cannot_override_method(self):
        jd = JsonData()
        jd.get = 1  # pylint: disable=all
        assert callable(jd.get)
        assert jd.get("get") == 1

    def test_class_decorator(self):
        @json_data_class
        class ClassWDefault(JsonData):
            b = 1
            a = 2

            def sum(self):
                return self.a + self.b

        @json_data_class
        class SubclassWDefault(ClassWDefault):
            c = 3

        assert ClassWDefault().b == 1
        assert ClassWDefault(b=2).b == 2
        assert ClassWDefault(a=9).sum() == 10
        inst = ClassWDefault()
        inst.sum = 4  # pylint: disable=all
        assert inst.sum() == 3
        assert inst.get("sum") == 4
        assert SubclassWDefault().stringify() == '{"a": 2, "b": 1, "c": 3}'

        json_ko_file = "/tmp/ulauncher-test/jsondata-key-order.json"
        inst = ClassWDefault.new_from_file(json_ko_file)
        inst.save()
        assert list(load_json(json_ko_file).keys()) == ["b", "a", "c"]

    def test_constructor_is_cloned(self):
        @json_data_class
        class ClassWDict(JsonData):
            subdict = {}

        inst = ClassWDict()
        inst.subdict["k"] = "v"
        assert ClassWDict().subdict.get("k") is None
        assert inst.subdict.get("k") == "v"

    def test_setitem_always_used(self):
        class UnderscorePrefix(JsonData):
            def __setitem__(self, key, value):
                super().__setitem__("_" + key, value)

        data = UnderscorePrefix({"one": 1})
        data.update(({"two": 2}))
        data.three = 3
        data["four"] = 4
        assert data.stringify(sort_keys=False) == '{"_one": 1, "_two": 2, "_three": 3, "_four": 4}'

    def test_file_cache(self):
        class C1(JsonData):
            pass

        class C2(JsonData):
            pass

        c1 = C1.new_from_file(json_file)
        c2a = C2.new_from_file(json_file)
        c2b = C2.new_from_file(json_file)
        c2a.uniqe_cache_key = 1
        assert not hasattr(c1, "uniqe_cache_key")
        assert hasattr(c2a, "uniqe_cache_key")
        assert hasattr(c2b, "uniqe_cache_key")
