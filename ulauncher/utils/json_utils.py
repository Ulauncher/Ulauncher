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


def json_load_dict(path: str | Path) -> dict[str, Any]:
    """The JSON object the file holds, or an empty dict if it holds none.

    An unreadable file still raises: that is not the same as having no data, and only the caller
    knows whether to reset what it already has.
    """
    file_path = Path(path).resolve()
    try:
        content = file_path.read_text().strip()
        # An empty file means an empty object, not a parse error that would get the file moved aside
        data = json.loads(content or "{}", object_hook=sanitize_json)
    except FileNotFoundError:
        return {}
    except ValueError:
        backup_path = f"{file_path}.{datetime.now().isoformat()}.backup"  # noqa: DTZ005 - local time reads better in a filename the user will find
        logger.exception('Error opening JSON file "%s"', file_path)
        logger.warning('Moving invalid JSON file to "%s"', backup_path)
        shutil.move(str(file_path), backup_path)
        return {}
    if not isinstance(data, dict):
        logger.warning('Expected a JSON object in "%s", got %s - file ignored', file_path, type(data).__name__)
        return {}
    return data


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
    """Save data to file path as JSON. Returns whether it was written, logging any failure."""
    file_path = Path(path).resolve()
    try:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        stringified_data = json_stringify(data, indent=indent, sort_keys=sort_keys, value_blacklist=value_blacklist)
        _atomic_write_text(file_path, stringified_data)
    # Serializing raises TypeError or ValueError depending on what the data holds, and writing
    # raises OSError. Callers only act on the bool, so treat every failure the same.
    except Exception:
        logger.exception('Could not write to JSON file "%s"', file_path)
        return False
    return True
