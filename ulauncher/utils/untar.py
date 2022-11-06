import tarfile
from os.path import exists
from shutil import rmtree


def untar(archive_path: str, output_path: str, overwrite=True, strip=0) -> None:
    if overwrite and exists(output_path):
        rmtree(output_path)

    with tarfile.open(archive_path, mode="r") as archive:
        for member in archive.getmembers():
            if member.path.startswith("/") or member.path.startswith("../"):
                raise Exception("Attempted Path Traversal in tar file")

            # Change member paths to strip N levels, like untar --strip-components=N
            member.path = member.path.split('/', strip)[-1]

        archive.extractall(output_path)
