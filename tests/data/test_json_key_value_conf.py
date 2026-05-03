from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Tuple

import pytest

from ulauncher.data import JsonConf, JsonKeyValueConf
from ulauncher.utils.json_utils import json_load, json_save


class TestJsonKeyValueConf:
    def test_save(self, tmp_path: Path) -> None:
        json_file = str(tmp_path / "jsonkvconf.json")

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

        store = Store.load(str(json_file))
        store["z"] = "last"
        store["a"] = "first"
        store.save()

        assert json_file.read_text() == '{\n  "z": "last",\n  "a": "first"\n}'

    def test_value_coercion(self, tmp_path: Path) -> None:
        json_file = str(tmp_path / "jsonkvconf.json")

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
        json_file = str(tmp_path / "jsonkvconf.json")

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
        json_file = str(tmp_path / "jsonkvconf.json")

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
        json_file = str(tmp_path / "jsonkvconf.json")

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
