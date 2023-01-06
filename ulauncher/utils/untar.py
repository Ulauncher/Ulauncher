import tarfile
import os
from shutil import rmtree
from pathlib import Path
from typing import Union


# This function is the same as Path.is_relative_to in 3.9, but we can't use that yet
def is_relative_to(child_path: Union[str, os.PathLike], root_path: Union[str, os.PathLike]):
    return Path(root_path).resolve() in Path(child_path).resolve().parents


def untar(archive_path: str, output_path: str, overwrite=True, strip=0) -> None:
    if overwrite and os.path.exists(output_path):
        rmtree(output_path)

    with tarfile.open(archive_path, mode="r") as archive:
        for member in archive.getmembers():
            # Tarfiles allow file names starting with "/", or containing "../" etc
            # See https://github.com/advisories/GHSA-gw9q-c7gh-j9vm
            if not is_relative_to(Path(output_path, member.name), output_path):
                # Normalise the path to just the basename
                strip = -1

            # Change member paths to strip N levels, like untar --strip-components=N
            member.path = member.path.split("/", strip)[-1]

        archive.extractall(output_path)
