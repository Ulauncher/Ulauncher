from __future__ import annotations

import logging
from contextlib import contextmanager
from pathlib import Path
from shutil import move, rmtree
from typing import Generator

logger = logging.getLogger(__name__)


def swap_dir(new_dir: str, target: str) -> bool:
    """Replace `target` with `new_dir`, rolling back to the original on failure. Returns whether it succeeded."""
    previous = f"{new_dir}.bak"
    # A stale .bak would be an existing dir, so move() nests target inside it instead of replacing.
    rmtree(previous, ignore_errors=True)
    backed_up = False
    if Path(target).exists():
        try:
            move(target, previous)
            backed_up = True
        except OSError:
            logger.exception("Could not back up the current version of %s; keeping it in place", target)
            rmtree(new_dir, ignore_errors=True)
            return False
    try:
        move(new_dir, target)
    except OSError:
        logger.exception("Could not swap extension into %s; keeping the previous version", target)
        # A cross-device move can fail after partially creating target; clear it before restoring.
        rmtree(target, ignore_errors=True)
        if backed_up:
            try:
                move(previous, target)
            except OSError:
                logger.exception("Could not restore the previous version of %s; it remains at %s", target, previous)
        rmtree(new_dir, ignore_errors=True)
        return False
    rmtree(previous, ignore_errors=True)
    return True


class StagingDir:
    """Fixed per-install staging dir with a shared prepare/use/discard lifecycle.

    The Gio callback chains cannot use a `with` block across async steps, so they drive
    this object explicitly: `prepare()` before downloading, `discard()` on every failure
    path. `commit()` marks the staging as consumed (swapped into place) so a later
    `discard()` will not delete anything. The synchronous call sites use `staging_dir()`.
    """

    def __init__(self, root: str, name: str) -> None:
        self.path = str(Path(root) / name)
        self._committed = False

    def prepare(self) -> str:
        """Clear any leftover from a prior failed install and recreate the staging dir.

        :raises OSError: if the staging dir cannot be recreated.
        """
        rmtree(self.path, ignore_errors=True)
        Path(self.path).mkdir(parents=True)
        return self.path

    def commit(self) -> None:
        """Mark the staging as consumed, so `discard()` becomes a no-op."""
        self._committed = True

    def discard(self) -> None:
        """Remove the staging dir, unless it was committed. Never raises."""
        if not self._committed:
            rmtree(self.path, ignore_errors=True)


@contextmanager
def staging_dir(root: str, name: str) -> Generator[StagingDir, None, None]:
    """Prepare a `StagingDir` and discard it on exit unless it was committed.

    :raises OSError: if the staging dir cannot be recreated.
    """
    staging = StagingDir(root, name)
    staging.prepare()
    try:
        yield staging
    finally:
        staging.discard()
