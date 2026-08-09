from __future__ import annotations

import json
import logging
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

logger = logging.getLogger(__name__)


# remove json nulls
def sanitize_json(d: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in d.items() if v is not None}


def _filter_recursive(data: Any, blacklist: Iterable[Any]) -> Any:
    if isinstance(data, dict):
        return {k: _filter_recursive(v, blacklist) for k, v in data.items() if v not in blacklist}
    if isinstance(data, list):
        return [_filter_recursive(v, blacklist) for v in data]
    return data


def json_load(path: str | Path) -> Any:
    file_path = Path(path).resolve()
    if file_path.is_file():
        try:
            data = file_path.read_text()
            if data.strip():
                return json.loads(data, object_hook=sanitize_json)
        except ValueError:
            backup_path = f"{file_path}.{datetime.now().isoformat()}.backup"
            logger.exception('Error opening JSON file "%s"', file_path)
            logger.warning('Moving invalid JSON file to "%s"', backup_path)
            shutil.move(str(file_path), backup_path)
    return {}  # pyrefly: ignore[implicit-any]


def json_stringify(
    data: Any, indent: int | str | None = None, sort_keys: bool = False, value_blacklist: Iterable[Any] | None = None
) -> str:
    filtered_data = data if value_blacklist is None else _filter_recursive(data, value_blacklist)
    return json.dumps(filtered_data, indent=indent, sort_keys=sort_keys)


def _atomic_write_text(file_path: Path, content: str) -> None:
    """Write to a temp file and rename, so readers never observe a partially written file."""
    # Sibling of the target so the rename stays on the same filesystem, and per-pid so that the app
    # and the cli never share a temp file.
    tmp_path = file_path.with_name(f".{file_path.name}.{os.getpid()}.tmp")
    try:
        tmp_path.write_text(content)
        if file_path.exists():
            # Replacing the target drops its mode along with its contents
            tmp_path.chmod(file_path.stat().st_mode & 0o777)
        os.replace(tmp_path, file_path)
    except OSError:
        tmp_path.unlink(missing_ok=True)
        raise


def json_save(
    data: Any,
    path: str | Path,
    indent: int | str | None = 2,
    sort_keys: bool = False,
    value_blacklist: Iterable[Any] | None = None,
) -> bool:
    """Save self to file path"""
    if file_path := Path(path).resolve():
        try:
            # Ensure parent dir first
            file_path.parent.mkdir(parents=True, exist_ok=True)
            stringified_data = json_stringify(data, indent=indent, sort_keys=sort_keys, value_blacklist=value_blacklist)
            _atomic_write_text(file_path, stringified_data)
        except OSError:
            logger.exception('Could not write to JSON file "%s"', file_path)
        else:
            return True
    return False
