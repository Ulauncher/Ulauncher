from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

import pytest

from ulauncher.utils.json_conf import JsonConf
from ulauncher.utils.json_utils import json_load, json_save, json_stringify

json_file = "/tmp/ulauncher-test/jsonconf.json"


class TestJsonConf:
    def setup_class(self) -> None:
        Path("/tmp/ulauncher-test").mkdir(parents=True, exist_ok=True)

    def teardown_class(self) -> None:
        shutil.rmtree("/tmp/ulauncher-test")

    def test_attr_methods(self) -> None:
        jc = JsonConf()
        assert not hasattr(jc, "a")
        with pytest.raises(AttributeError):
            jc.a  # noqa: B018
        jc.a = False
        assert hasattr(jc, "a")
        assert jc.a is False

    def test_setting_and_comparison(self) -> None:
        jc = JsonConf()
        jc.a = 1
        jc.update({"b": 2}, c=3)
        jc["d"] = 4
        assert jc == JsonConf(a=1, b=2, c=3, d=4)
        assert JsonConf(b=2, a=1) == JsonConf({"a": 1, "b": 2})
        assert JsonConf(a=1, b=2) != JsonConf({"a": 1})

    def test_new_file_file_cache(self) -> None:
        file_path = "/tmp/ulauncher-test/jsonconf_test_cache.json"
        jc1 = JsonConf.load(file_path)
        assert not hasattr(jc1, "a")
        jc1.a = 1
        jc2 = JsonConf.load(file_path)
        assert id(jc2) == id(jc1)  # tests that it's actually the same object in memory
        assert jc2.a == 1

    def test_stringify(self) -> None:
        assert json_stringify(JsonConf(a=1, c=3, b=2)) == '{"a": 1, "b": 2, "c": 3}'
        assert json_stringify(JsonConf(a=1, c=3, b=2), sort_keys=False) == '{"a": 1, "c": 3, "b": 2}'
        assert json_stringify(JsonConf(a=1, b=2), indent=4) == '{\n    "a": 1,\n    "b": 2\n}'
        conf = JsonConf(a=None, b=[], c={}, d=1)
        assert json_stringify(conf) == '{"d": 1}'
        assert json_stringify(conf, value_blacklist=[]) == '{"a": null, "b": [], "c": {}, "d": 1}'

    def test_save(self) -> None:
        jc = JsonConf.load(json_file)
        jc.asdf = "xyz"
        jc.save()
        assert json_load(json_file).get("asdf") == "xyz"
        jc.update(asdf="zyx")
        jc.save()
        assert json_load(json_file).get("asdf") == "zyx"
        jc.save(asdf="yxz")
        assert json_load(json_file).get("asdf") == "yxz"
        jc.save({"asdf": "xzy"})
        assert json_load(json_file).get("asdf") == "xzy"

    def test_save_external(self) -> None:
        # Check that JsonConf initiated w or w/o path saves to the path specified,
        # not the instance path
        file_path = "/tmp/ulauncher-test/jsonconf_save_as.json"
        jc_static = JsonConf(abc=123)
        json_save(jc_static, file_path)
        assert json_load(file_path).get("abc") == 123
        jc = JsonConf.load(json_file)
        jc.save()
        jc.bcd = 234
        json_save(jc, file_path)
        assert json_load(file_path).get("abc") is None
        assert json_load(file_path).get("bcd") == 234
        assert json_load(json_file).get("bcd") is None

    def test_cannot_override_method(self) -> None:
        jc = JsonConf()
        with pytest.raises(KeyError):
            jc.get = 1  # type: ignore[assignment, method-assign]
        assert callable(jc.get)

    def test_inheritance(self) -> None:
        class ClassWDefault(JsonConf):
            b = 1
            a = 2

            def sum(self) -> int:
                return self.a + self.b

        class SubclassWDefault(ClassWDefault):
            c = 3

        assert ClassWDefault().b == 1
        assert ClassWDefault(b=2).b == 2
        assert ClassWDefault(a=9).sum() == 10
        inst = ClassWDefault()
        assert inst.sum() == 3
        assert json_stringify(SubclassWDefault()) == '{"a": 2, "b": 1, "c": 3}'

        json_ko_file = "/tmp/ulauncher-test/jsonconf-key-order.json"
        inst = ClassWDefault.load(json_ko_file)
        inst.save()
        assert list(json_load(json_ko_file).keys()) == ["a", "b"]

    def test_constructor_is_cloned(self) -> None:
        class ClassWDict(JsonConf):
            subdict: dict[str, str] = {}

        inst = ClassWDict()
        inst.subdict["k"] = "v"
        assert ClassWDict().subdict.get("k") is None
        assert inst.subdict.get("k") == "v"

    def test_setitem_always_used(self) -> None:
        class UnderscorePrefix(JsonConf):
            def __setitem__(self, key: str, value: Any, validate_type: bool = True) -> None:
                super().__setitem__("_" + key, value, validate_type)

        data = UnderscorePrefix({"one": 1})
        data.update({"two": 2})
        data.three = 3
        data["four"] = 4
        assert json_stringify(data, sort_keys=False) == '{"_one": 1, "_two": 2, "_three": 3, "_four": 4}'

    def test_file_cache(self) -> None:
        class C1(JsonConf):
            pass

        class C2(JsonConf):
            pass

        c1 = C1.load(json_file)
        c2a = C2.load(json_file)
        c2b = C2.load(json_file)
        c2a.unique_cache_key = 1
        assert not hasattr(c1, "unique_cache_key")
        assert hasattr(c2a, "unique_cache_key")
        assert hasattr(c2b, "unique_cache_key")

    def test_load_always_reads_file(self) -> None:
        class C1(JsonConf):
            pass

        c1 = C1.load(json_file)
        c1.a = 1
        c1.save()

        # write a different value directly to the file
        with open(json_file, "w") as f:
            f.write('{"a": 2}')

        # load again
        c1 = C1.load(json_file)
        assert c1.a == 2  # should read the value from the file, not the cached instance
