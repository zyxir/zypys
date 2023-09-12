"""
This module sync my World of Warcraft settings.

It compares the last modified time of my local game settings with the cloud
backup, and do backup or restoration based on which one is newer.
"""

import shutil
import zipfile
from pathlib import Path
from typing import List


def _last_modified_time(path: Path) -> float:
    return path.stat().st_mtime


def last_modified_time(path: Path) -> float:
    """Get the last modified time of `p`.

    If `p` is a directory, get the newest modified time of the files within.
    """
    if path.is_file():
        return _last_modified_time(path)
    elif path.is_dir():
        mtimes = [_last_modified_time(path)]
        for p in path.glob("**/*"):
            mtimes.append(p.stat().st_mtime)
        return max(mtimes)
    else:
        return 0


def backup(game_path: Path, dirs: List[str], backup_path: Path):
    """Backup directories under game path into a single archive."""
    # Delete backup if already exists.
    backup_path.unlink(missing_ok=True)
    # Make the archive.
    with zipfile.ZipFile(backup_path, "w", compression=zipfile.ZIP_LZMA) as zf:
        # Add everything needed into the archive.
        for d in dirs:
            subdir = game_path.joinpath(d)
            for path in subdir.glob("**/*"):
                if path.is_file():
                    relative_path = path.relative_to(game_path)
                    zf.write(path, arcname=relative_path)


def restore(game_path: Path, dirs: List[str], backup_path: Path):
    """Restore backup into the game path."""
    # Delete relevant directories if already exists.
    for d in dirs:
        subdir = game_path.joinpath(d)
        if subdir.exists():
            shutil.rmtree(subdir)
    # Restore the archive.
    with zipfile.ZipFile(backup_path, "r") as zf:
        zf.extractall(game_path)
