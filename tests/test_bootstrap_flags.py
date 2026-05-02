from __future__ import annotations

import importlib
import os
from collections.abc import Generator

import pytest

import ulauncher


class TestBootstrapFlags:
    @pytest.fixture(autouse=True)
    def reload_ulauncher(self) -> Generator[None, None, None]:
        yield
        importlib.reload(ulauncher)

    def test_first_run_flags_are_snapshotted_at_import(self, monkeypatch: pytest.MonkeyPatch) -> None:
        config_path = ulauncher.paths.CONFIG
        state_path = ulauncher.paths.STATE

        def exists(path: str) -> bool:
            return path not in (config_path, state_path)

        monkeypatch.setattr(os.path, "exists", exists)
        importlib.reload(ulauncher)

        assert ulauncher.first_run is True
        assert ulauncher.first_v6_run is True

        monkeypatch.setattr(os.path, "exists", lambda _path: True)

        assert ulauncher.first_run is True
        assert ulauncher.first_v6_run is True

    def test_first_run_flags_capture_config_and_state_independently(self, monkeypatch: pytest.MonkeyPatch) -> None:
        state_path = ulauncher.paths.STATE

        def exists(path: str) -> bool:
            return path != state_path

        monkeypatch.setattr(os.path, "exists", exists)
        importlib.reload(ulauncher)

        assert ulauncher.first_run is False
        assert ulauncher.first_v6_run is True
