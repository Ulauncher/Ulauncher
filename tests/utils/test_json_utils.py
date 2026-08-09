from __future__ import annotations

import os
from pathlib import Path

import pytest

from ulauncher.utils.json_utils import json_load_dict, json_save


class TestJsonSave:
    def test_preserves_existing_file_mode(self, tmp_path: Path) -> None:
        json_file = tmp_path / "conf.json"
        assert json_save({"a": 1}, json_file)
        json_file.chmod(0o600)

        assert json_save({"a": 2}, json_file)

        assert json_file.stat().st_mode & 0o777 == 0o600
        assert json_load_dict(json_file) == {"a": 2}

    def test_leaves_no_temp_file_behind(self, tmp_path: Path) -> None:
        json_file = tmp_path / "conf.json"

        assert json_save({"a": 1}, json_file)

        assert [f.name for f in tmp_path.iterdir()] == ["conf.json"]

    def test_keeps_previous_content_when_the_write_fails(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        json_file = tmp_path / "conf.json"
        assert json_save({"a": 1}, json_file)

        def fail(*_args: object, **_kwargs: object) -> None:
            msg = "no space left on device"
            raise OSError(msg)

        monkeypatch.setattr(os, "replace", fail)
        assert not json_save({"a": 2}, json_file)

        assert json_load_dict(json_file) == {"a": 1}
        assert [f.name for f in tmp_path.iterdir()] == ["conf.json"]
