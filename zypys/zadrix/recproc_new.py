"""This module processes my Minecraft recordings.

With a source directory containing recordings and a target directory, it can:

1. Compresses recordings, and move the compressed files into the target
directory.

2. Extract highlights as smaller videos, and move them into the target
directory.

3. Copy all timelapse videos generated by Replay Mod to the target directory.

This module is made with functional programming paradim.  All video manipulation
is done with FFmpeg.
"""

import datetime
import logging
import os
import re
import subprocess
from itertools import starmap
from pathlib import Path
from typing import List

# ------------------------------------------------------------------------------
# File recognition
# ------------------------------------------------------------------------------

# Regular expression indicating a recording.
RE_RECORDING = re.compile("^[0-9]+_day[0-9]+_.*\\.(mp4|mov|mkv)$")

# Regular expression extracting index from a recording.
RE_INDEX = re.compile("^([0-9]+).*$")

# Regular expression indicating a timelapse video.
RE_TIMELAPSE = re.compile("^[0-9]+[a-z]+_.*\\.(mp4|mov|mkv)")


def is_recording(file: Path) -> bool:
    """Return true if file is a recoding."""
    return file.is_file() and RE_RECORDING.fullmatch(file.name) is not None


def is_timelapse(file: Path) -> bool:
    """Return true if file is a timelapse."""
    return file.is_file() and RE_TIMELAPSE.fullmatch(file.name) is not None


def get_index(file: Path) -> int:
    """Get the index of a recording or a timelapse.

    Return -1 if no index is found.
    """
    match = RE_INDEX.search(file.name)
    if match is None:
        return 0
    return int(match.group(1))


def get_recordings(directory: Path) -> List[Path]:
    """Get the list of recordings contained in a directory.

    Recordings are sorted with their indices.
    """
    recordings = list(filter(is_recording, directory.iterdir()))
    recordings = sorted(recordings, key=get_index)
    return recordings


def get_timelapses(directory: Path) -> List[Path]:
    """Get the list of timelapses contained in a directory."""
    return list(filter(is_timelapse, directory.iterdir()))


# ------------------------------------------------------------------------------
# Compressing.
# ------------------------------------------------------------------------------


def compress(in_file: Path, out_file: Path):
    """Compress one file with FFmpeg.

    If silent is True, do not print thet command used.

    Can be interrupted by Ctrl-C.
    """
    cmd = (
        f'ffmpeg -i "{in_file}" -loglevel warning '
        "-preset medium -c:v libx265 -crf 28 "
        f'-s 1280x720 -filter:v fps=30 "{out_file}"'
    )
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.stderr is not None:
        for line in result.stderr.splitlines():
            logging.warning(line)


def compress_all(in_dir: Path, out_dir: Path, maxnum: int = 0):
    """Compress all recordings in in_dir, printing info.

    Compressed recordings are put into out_dir.

    Compress maxnum recordings at most.  If maxnum is 0, compress all
    recordings.
    """
    in_files = get_recordings(in_dir)
    out_files = list(map(lambda in_file: out_dir.joinpath(in_file.name), in_files))
    if maxnum == 0:
        maxnum = len(in_files)
    print(f"{len(in_files)} recordings found, {maxnum} recordings to compress.")
    for i, (in_file, out_file) in enumerate(zip(in_files, out_files)):
        if i >= maxnum:
            break
        # Print info without newline.
        now = datetime.datetime.now().strftime("%H:%M")
        info = f'Start compressing "{in_file.name}" at {now} ({i}/{maxnum})...'
        print(info, end="", flush=True)
        info_finished = False
        try:
            # Compress the file.
            compress(in_file, out_file)
            # Finish the info.
            print("done")
            info_finished = True
        except KeyboardInterrupt:
            # When compressing is interrupted, delete the incomplete output
            # file.
            if not info_finished:
                print("")
            print("Compressing interrupted by Ctrl-C.")
            out_file.unlink(missing_ok=True)
            break


if __name__ == "__main__":
    in_dir = Path("d:/zadrix-records/500days/")
    out_dir = Path("tmp")
    compress_all(in_dir, out_dir)
