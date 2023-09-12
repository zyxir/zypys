"""
This module sync my World of Warcraft settings.

It compares the last modified time of my local game settings with the cloud
backup, and do backup or restoration based on which one is newer.
"""

import shutil
import zipfile
from pathlib import Path
import logging
from typing import List


def _modified_time(path: Path) -> float:
    return path.stat().st_mtime


def modified_time(path: Path) -> float:
    """Get the last modified time of `p`.

    If `p` is a directory, get the newest modified time of the files within.
    """
    if path.is_file():
        return _modified_time(path)
    elif path.is_dir():
        mtimes = [_modified_time(path)]
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


def sync(game_path: Path, dirs: List[str], backup_path: Path) -> int:
    """Do backup or restore based on modified time."""
    # Check for game path.
    if not game_path.exists():
        logging.error(f"Game path \"{game_path}\" does not exist!")
        return 1
    # Decide an action.
    if not backup_path.exists():
        action = "backup"
    else:
        game_modified_time = modified_time(game_path)
        backup_modified_time = modified_time(backup_path)
        if game_modified_time > backup_modified_time:
            action = "backup"
        elif game_modified_time < backup_modified_time:
            action = "restore"
        else:
            action = "nothing"

    # Do an action.
    if action == "backup":
        logging.info("Backing up game settings.")
        backup(game_path, dirs, backup_path)
        logging.info("Work complete.")
    elif action == "restore":
        logging.info("Restoring game settings.")
        restore(game_path, dirs, backup_path)
        logging.info("Work complete.")
    else:
        logging.info("Nothing to do.")
    return 0


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    game_path = Path("c:/Program Files (x86)/World of Warcraft/_retail_/")
    dirs = ["Interface", "WTF"]
    backup_path = Path("c:/Users/zyxir/Zybox/wowui.zip")
    sync(game_path, dirs, backup_path)
