"""
This module sync my World of Warcraft settings.

It compares the last modified time of my local game settings with the cloud
backup, and do backup or restoration based on which one is newer.
"""

import os
import shutil
import subprocess
from pathlib import Path
from typing import List


def get_mtime(p: Path) -> float:
    """Get the newest modified time under a tree."""
    if p.exists():
        mtimes = [p.stat().st_mtime]
        if p.is_dir():
            for sub in p.iterdir():
                mtimes.append(get_mtime(sub))
        return max(mtimes)
    else:
        return 0


def compress(main_path: Path, dirs: List[str], archive_path: Path):
    """Compress `dirs` in `main_path` into `archive_path`.

    This requires that one of "7-zip" or "NanaZip" is installed.
    """
    # Change directory.
    orig_dir = os.getcwd()
    os.chdir(main_path)
    # Compress with the "7z" command.
    cmd = ["7z", "a", "-t7z", str(archive_path)] + dirs
    proc = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True
    )
    stdout = proc.stdout
    if stdout is not None:
        for line in stdout:
            print(f"[7z] {line}")
    proc.wait()
    # Return to the original directory.
    os.chdir(orig_dir)


def extract(archive_path: Path, main_path: Path):
    """Extract compressed archive `archive_path` to `main_path`."""
    # Change directory.
    orig_dir = os.getcwd()
    os.chdir(main_path)
    # Extract with the "7z" command.
    cmd = ["7z", "x", str(archive_path)]
    proc = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True
    )
    stdout = proc.stdout
    if stdout is not None:
        for line in stdout:
            print(f"[7z] {line}", end="")
    proc.wait()
    # Return to the original directory.
    os.chdir(orig_dir)


def backup(game_path: Path, dirs: List[str], backup_path: Path):
    """Backup directories under game path into a single archive."""
    if backup_path.exists():
        print("Backing up the old backup...")
        new_name = backup_path.stem + "_old" + backup_path.suffix
        new_path = backup_path.parent.joinpath(new_name)
        new_path.unlink(missing_ok=True)
        backup_path.rename(new_path)
    print("Creating the new backup...")
    compress(game_path, dirs, backup_path)
    print("Work complete.")


def restore(game_path: Path, dirs: List[str], backup_path: Path):
    """Restore backup into the game path."""
    if any(map(lambda d: game_path.joinpath(d).exists, dirs)):
        print("Backing up game settings...")
        new_name = backup_path.stem + "_old" + backup_path.suffix
        new_path = game_path.joinpath(new_name)
        new_path.unlink(missing_ok=True)
        compress(game_path, dirs, new_path)
        for d in dirs:
            subdir = game_path.joinpath(d)
            shutil.rmtree(subdir, ignore_errors=True)
    print("Restoring backup...")
    extract(backup_path, game_path)
    print("Work complete.")


def do_nothing(*args):
    """Ignore arguments and do nothing."""
    pass


def sync(game_path: Path, dirs: List[str], backup_path: Path) -> int:
    """Do backup or restore based on modified time."""
    # Check for game path.
    if not game_path.exists():
        print(f'Game path "{game_path}" does not exist!')
        return 1
    # Decide an action.
    if not backup_path.exists():
        default_action = "backup"
    else:
        game_mtime = max(map(lambda d: get_mtime(game_path.joinpath(d)), dirs))
        backup_mtime = get_mtime(backup_path)
        if game_mtime > backup_mtime:
            default_action = "backup"
        elif game_mtime < backup_mtime:
            default_action = "restore"
        else:
            default_action = "do nothing"
    answer = input(f"I am going to {default_action}, shall I proceed? [Y/n] ")
    while answer not in ["", "y", "Y", "n", "N"]:
        answer = input("Please answer [y] or [n]: ")
    if answer in ["", "y", "Y"]:
        action = default_action
    else:
        answer = input("Then what should I do instead? ([B]ackup/[R]estore/[N]othing) ")
        if answer in ["b", "B"]:
            action = "backup"
        elif answer in ["r", "R"]:
            action = "restore"
        else:
            action = "do nothing"

    # Do an action.
    action_dict = {
        "backup": backup,
        "restore": restore,
    }
    fn = action_dict.get(action, do_nothing)
    fn(game_path, dirs, backup_path)
    return 0


if __name__ == "__main__":
    main_path = Path("c:/Program Files (x86)/World of Warcraft/_retail_/")
    dirs = ["Interface", "WTF"]
    archive_path = Path("c:/Users/zyxir/Zybox/wowui.zip")
    sync(main_path, dirs, archive_path)
