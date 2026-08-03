from __future__ import annotations

import json
from pathlib import Path

from ulauncher.modes.extensions.extension_record import ExtensionRecord


def test_seed_default_state__applies_the_bundled_defaults(tmp_path: Path) -> None:
    (tmp_path / ".default-state.json").write_text(json.dumps({"is_enabled": False, "url": "https://example.com"}))
    record = ExtensionRecord("test_record_seeds_defaults", str(tmp_path))

    assert record.state.is_enabled is False
    assert record.state.url == "https://example.com"


def test_seed_default_state__ignores_keys_the_state_rejects(tmp_path: Path) -> None:
    (tmp_path / ".default-state.json").write_text(json.dumps({"is_enabled": False, "save": "shadows a method"}))
    record = ExtensionRecord("test_record_ignores_rejected_defaults", str(tmp_path))

    assert record.state.is_enabled is False
    assert "save" not in record.state
