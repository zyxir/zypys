"""
This module sync my World of Warcraft settings.

It compares the last modified time of my local game settings with the cloud
backup, and do backup or restoration based on which one is newer.
"""

import logging
import shutil
import zipfile
from pathlib import Path
from typing import List

from tqdm import tqdm


def _modified_time_single_file(path: Path) -> float:
    return path.stat().st_mtime


def _modified_time(path: Path) -> float:
    """Get the last modified time of `path`.

    If `p` is a directory, get the newest modified time of the files within.
    """
    if path.is_file():
        return _modified_time_single_file(path)
    elif path.is_dir():
        mtimes = [_modified_time_single_file(path)]
        for p in path.glob("**/*"):
            mtimes.append(p.stat().st_mtime)
        return max(mtimes)
    else:
        return 0


def modified_time(path: Path, dirs: List[str] = []) -> float:
    """Get the newest modified time of `path` and the files within.

    If `dirs` is not empty, get the newest modified time of these subdirectories
    instead.
    """
    if len(dirs):
        def subdir_modified_time(d):
            subdir = path.joinpath(d)
            return _modified_time(subdir) if subdir.is_dir() else 0
        return max(map(subdir_modified_time, dirs))
    else:
        return _modified_time(path)


def make_archive(main_path: Path, dirs: List[str], archive_path: Path):
    """Compress `dirs` in `main_path` into an archive."""
    with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_LZMA) as zf:
        # Add everything needed into the archive.
        for d in dirs:
            subdir = main_path.joinpath(d)
            paths = subdir.glob("**/*")
            path_sizes = map(lambda p: p.stat().st_size, paths)
            with tqdm(total=sum(path_sizes), unit="bit") as pbar:
                for path, size in zip(paths, path_sizes):
                    if path.is_file():
                        relative_path = path.relative_to(main_path)
                        zf.write(path, arcname=relative_path)
                        pbar.update(size)


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
        logging.error(f'Game path "{game_path}" does not exist!')
        return 1
    # Decide an action.
    if not backup_path.exists():
        action = "backup"
    else:
        game_modified_time = modified_time(game_path, dirs)
        backup_modified_time = modified_time(backup_path)
        if game_modified_time > backup_modified_time:
            default_action = "backup"
        elif game_modified_time < backup_modified_time:
            default_action = "restore"
        else:
            default_action = "do nothing"
        answer = input(f"I am going to {default_action}, shall I proceed? [Y/n] ")
        while answer not in ["", "y", "Y", "n", "N"]:
            answer = input("Please answer [y] or [n]: ")
        if answer in ["", "y", "Y"]:
            action = default_action
        else:
            answer = input("Then what should I do instead? [B]ackup/[R]estore/[N]othing")
            if answer in ["b", "B"]:
                action = "backup"
            elif answer in ["r", "R"]:
                action = "restore"
            else:
                action = "do nothing"

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
