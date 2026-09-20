from __future__ import annotations

import io
import tarfile
from pathlib import Path

import pytest

from ulauncher.utils.untar import untar


def add_file(archive: tarfile.TarFile, name: str, content: bytes = b"data") -> None:
    info = tarfile.TarInfo(name)
    info.size = len(content)
    archive.addfile(info, io.BytesIO(content))


def add_symlink(archive: tarfile.TarFile, name: str, target: str) -> None:
    info = tarfile.TarInfo(name)
    info.type = tarfile.SYMTYPE
    info.linkname = target
    archive.addfile(info)


def test_extracts_files_and_strips_components(tmp_path: Path) -> None:
    archive_path = tmp_path / "archive.tar"
    with tarfile.open(archive_path, "w") as archive:
        add_file(archive, "repo-main/hello.txt", b"hi")
        add_file(archive, "repo-main/sub/nested.txt", b"nested")

    output = tmp_path / "out"
    untar(str(archive_path), str(output), strip=1)

    assert (output / "hello.txt").read_bytes() == b"hi"
    assert (output / "sub" / "nested.txt").read_bytes() == b"nested"


def test_relative_symlinks_are_preserved(tmp_path: Path) -> None:
    archive_path = tmp_path / "archive.tar"
    with tarfile.open(archive_path, "w") as archive:
        add_file(archive, "US.svg", b"<svg/>")
        add_symlink(archive, "USD.svg", "US.svg")

    output = tmp_path / "out"
    untar(str(archive_path), str(output))

    assert (output / "USD.svg").is_symlink()
    assert (output / "USD.svg").resolve() == (output / "US.svg").resolve()


@pytest.mark.skipif(not hasattr(tarfile, "data_filter"), reason="tarfile.data_filter is unavailable")
def test_links_escaping_the_output_dir_are_rejected(tmp_path: Path) -> None:
    archive_path = tmp_path / "archive.tar"
    with tarfile.open(archive_path, "w") as archive:
        add_symlink(archive, "abs", "/etc/passwd")
        add_symlink(archive, "rel", "../../etc/passwd")

    with pytest.raises(tarfile.FilterError):
        untar(str(archive_path), str(tmp_path / "out"))
