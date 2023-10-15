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


def make_archive(main_path: Path, dirs: List[str], archive_path: Path):
    """Compress `dirs` in `main_path` into an archive."""
    with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_LZMA) as zf:
        # Add everything needed into the archive.
        for d in dirs:
            subdir = main_path.joinpath(d)
            for path in subdir.glob("**/*"):
                if path.is_file():
                    relative_path = path.relative_to(main_path)
                    zf.write(path, arcname=relative_path)


def backup(game_path: Path, dirs: List[str], backup_path: Path):
    """Backup directories under game path into a single archive."""
    # Rename backup if already exists.
    if backup_path.exists():
        new_name = backup_path.stem + "_old" + backup_path.suffix
        new_path = backup_path.parent.joinpath(new_name)
        new_path.unlink(missing_ok=True)
        backup_path.rename(new_path)
    # Make the archive.
    make_archive(game_path, dirs, backup_path)


def restore(game_path: Path, dirs: List[str], backup_path: Path):
    """Restore backup into the game path."""
    # Backup relevant directories if already exists.
    if any(map(lambda d: game_path.joinpath(d).exists, dirs)):
        new_name = backup_path.stem + "_old" + backup_path.suffix
        new_path = game_path.joinpath(new_name)
        new_path.unlink(missing_ok=True)
        make_archive(game_path, dirs, new_path)
        for d in dirs:
            subdir = game_path.joinpath(d)
            shutil.rmtree(subdir, ignore_errors=True)
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
    main_path = Path("c:/Program Files (x86)/World of Warcraft/_retail_/")
    dirs = ["Interface", "WTF"]
    archive_path = Path("c:/Users/zyxir/Zybox/wowui.zip")
    sync(main_path, dirs, archive_path)