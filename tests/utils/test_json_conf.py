from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Tuple

import pytest

from ulauncher.utils.json_conf import JsonConf, JsonKeyValueConf
from ulauncher.utils.json_utils import json_load, json_save, json_stringify


class TestJsonConf:
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
        jc["d"] = 4  # type: ignore[assignment]
        assert jc == JsonConf(a=1, b=2, c=3, d=4)
        assert JsonConf(b=2, a=1) == JsonConf({"a": 1, "b": 2})
        assert JsonConf(a=1, b=2) != JsonConf({"a": 1})

    def test_new_file_file_cache(self, tmp_path: Path) -> None:
        """Test that JsonConf.load uses file cache for the same path"""
        file_path = tmp_path / "jsonconf_test_cache.json"

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

    def test_save(self, tmp_path: Path) -> None:
        """Test that save() writes the correct data using json_save"""
        json_file = tmp_path / "jsonconf.json"

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

    def test_save_external(self, tmp_path: Path) -> None:
        """Test saving to external paths"""
        json_file = tmp_path / "jsonconf.json"
        file_path = tmp_path / "jsonconf_save_as.json"

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

    def test_inheritance(self, tmp_path: Path) -> None:
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

        # Test file operations with real files
        json_ko_file = tmp_path / "jsonconf-key-order.json"
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

    def test_file_cache(self, tmp_path: Path) -> None:
        """Test that different JsonConf subclasses maintain separate file caches"""
        json_file = tmp_path / "jsonconf.json"

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

    def test_load_always_reads_file(self, tmp_path: Path) -> None:
        """Test that load() always reads from file and updates cached instance"""
        json_file = tmp_path / "jsonconf.json"

        class C1(JsonConf):
            pass

        # Create initial file with data
        json_save({"a": 1}, json_file)

        # Load and verify
        c1 = C1.load(json_file)
        assert c1.a == 1

        # Write a different value directly to the file
        json_save({"a": 2}, json_file)

        # Load again - should read the new value and update the cached instance
        c1_again = C1.load(json_file)
        assert c1_again.a == 2
        # Since it's the same cached instance, the original reference should also be updated
        assert c1.a == 2
        assert id(c1) == id(c1_again)


class TestJsonKeyValueConf:
    def test_save(self, tmp_path: Path) -> None:
        json_file = tmp_path / "jsonkvconf.json"

        class Store(JsonKeyValueConf[str, str]):
            pass

        store = Store.load(json_file)
        store["asdf"] = "xyz"
        store.save()
        assert json_load(json_file).get("asdf") == "xyz"

        store.save({"asdf": "zyx"})
        assert json_load(json_file).get("asdf") == "zyx"

        store.save(asdf="yxz")
        assert json_load(json_file).get("asdf") == "yxz"

    def test_save_preserves_insertion_order(self, tmp_path: Path) -> None:
        json_file = tmp_path / "jsonkvconf.json"

        class Store(JsonKeyValueConf[str, str]):
            pass

        store = Store.load(json_file)
        store["z"] = "last"
        store["a"] = "first"
        store.save()

        assert json_file.read_text() == '{\n  "z": "last",\n  "a": "first"\n}'

    def test_value_coercion(self, tmp_path: Path) -> None:
        json_file = tmp_path / "jsonkvconf.json"

        class Record(JsonConf):
            value = ""

        class Store(JsonKeyValueConf[str, Record]):
            pass

        store = Store.load(json_file)
        store["one"] = {"value": "1"}
        assert isinstance(store["one"], Record)
        assert store["one"].value == "1"

        store.save()
        assert json_load(json_file) == {"one": {"value": "1"}}

    def test_none_value_deletes_key(self) -> None:
        class Store(JsonKeyValueConf[str, str]):
            pass

        store = Store({"custom": "value"})

        store["custom"] = None

        assert "custom" not in store

        store["custom"] = None

    def test_accepts_existing_value_instances(self) -> None:
        class Record(JsonConf):
            value = ""

        class Store(JsonKeyValueConf[str, Record]):
            pass

        record = Record(value="1")
        store = Store({"record": record})

        assert store["record"] == record

    def test_infers_runtime_coercion_from_generic_value_type(self) -> None:
        class Record(JsonConf):
            value = ""

        class Store(JsonKeyValueConf[str, Record]):
            pass

        assert Store._value_type is Record

    def test_setitem_coerces_raw_values(self) -> None:
        class Store(JsonKeyValueConf[str, Path]):
            pass

        store = Store({"a": "/tmp/a"})
        store["b"] = "/tmp/b"

        assert store["a"] == Path("/tmp/a")
        assert store["b"] == Path("/tmp/b")

    def test_file_cache(self, tmp_path: Path) -> None:
        json_file = tmp_path / "jsonkvconf.json"

        class C1(JsonKeyValueConf[str, str]):
            pass

        class C2(JsonKeyValueConf[str, str]):
            pass

        c1 = C1.load(json_file)
        c2a = C2.load(json_file)
        c2b = C2.load(json_file)
        c2a["unique_cache_key"] = "1"
        assert "unique_cache_key" not in c1
        assert "unique_cache_key" in c2a
        assert "unique_cache_key" in c2b

    def test_load_always_reads_file(self, tmp_path: Path) -> None:
        json_file = tmp_path / "jsonkvconf.json"

        class Store(JsonKeyValueConf[str, int]):
            pass

        json_save({"a": 1}, json_file)

        store = Store.load(json_file)
        assert store["a"] == 1

        json_save({"a": 2}, json_file)

        store_again = Store.load(json_file)
        assert store_again["a"] == 2
        assert store["a"] == 2
        assert id(store) == id(store_again)

    def test_raises_on_invalid_type_arguments(self) -> None:
        with pytest.raises(TypeError, match="key type must be str"):

            class NonStrKey(JsonKeyValueConf[int, str]):  # type: ignore[type-arg]
                pass

        with pytest.raises(TypeError, match="concrete type"):

            class ForwardRefValue(JsonKeyValueConf[str, "str"]):  # type: ignore[type-arg]
                pass

        with pytest.raises(TypeError, match="concrete type"):

            class NoGenerics(JsonKeyValueConf):  # type: ignore[type-arg]
                pass

        with pytest.raises(TypeError, match="unparameterized"):

            class UnparamList(JsonKeyValueConf[str, list]):  # type: ignore[type-arg]
                pass

        with pytest.raises(TypeError, match="unparameterized"):

            class UnparamDict(JsonKeyValueConf[str, dict]):  # type: ignore[type-arg]
                pass

        with pytest.raises(TypeError, match="unsupported parameterized"):

            class TupleValue(JsonKeyValueConf[str, Tuple[str, int]]):  # type: ignore[type-arg]
                pass

    def test_primitive_value_types_accepted(self) -> None:
        class StrStore(JsonKeyValueConf[str, str]):
            pass

        class IntStore(JsonKeyValueConf[str, int]):
            pass

        s = StrStore()
        s["key"] = "hello"
        assert s["key"] == "hello"

        i = IntStore()
        i["key"] = 42
        assert i["key"] == 42

    def test_parameterized_list_and_dict_accepted(self) -> None:
        class ListStore(JsonKeyValueConf[str, List[int]]):
            pass

        class DictStore(JsonKeyValueConf[str, Dict[str, int]]):
            pass

        ls = ListStore()
        ls["nums"] = [1, 2, 3]
        assert ls["nums"] == [1, 2, 3]

        ds = DictStore()
        ds["mapping"] = {"a": 1}
        assert ds["mapping"] == {"a": 1}

    def test_coerce_value_skips_if_already_correct_type(self) -> None:
        class PathStore(JsonKeyValueConf[str, Path]):
            pass

        store = PathStore()
        existing = Path("/tmp/test")
        store["key"] = existing
        assert store["key"] is existing

    def test_subclass_of_subclass_coerces_values(self) -> None:
        class Store(JsonKeyValueConf[str, Path]):
            pass

        class SubStore(Store):
            pass

        sub = SubStore()
        sub["key"] = "/tmp/test"  # type: ignore[assignment]
        assert isinstance(sub["key"], Path)

    def test_load_removes_deleted_keys(self, tmp_path: Path) -> None:
        json_file = tmp_path / "jsonkvconf.json"

        class Store(JsonKeyValueConf[str, int]):
            pass

        json_save({"a": 1, "b": 2}, json_file)

        store = Store.load(json_file)
        assert dict(store.items()) == {"a": 1, "b": 2}

        json_save({"a": 3}, json_file)

        store_again = Store.load(json_file)
        assert dict(store_again.items()) == {"a": 3}
        assert dict(store.items()) == {"a": 3}
        assert id(store) == id(store_again)
