"""Unit tests of recproc.py

These tests apply functions in the module to a set of demo videos, trying to
validate the module as much as possible.
"""

import logging
import subprocess
from pathlib import Path
import tempfile
from typing import Tuple

from zypys.zadrix import recproc

# The directory of demo videos.
demo_dir = Path("tests/zadrix/test_recproc_demo_videos")


def get_video_duration(video: Path) -> float:
    """Get the duration of video with ffprobe.

    If the command fails, return -1.
    """
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        str(video),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.stdout is not None:
        for line in result.stderr.splitlines():
            logging.warning(line)
    if result.returncode != 0:
        return -1
    return float(result.stdout)


def get_video_resolution(video: Path) -> Tuple[int, int]:
    """Get the width and height of video with ffprobe.

    If the command fails, return -1 and -1.
    """
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "stream=width,height",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        str(video),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.stdout is not None:
        for line in result.stderr.splitlines():
            logging.warning(line)
    if result.returncode != 0:
        return -1, -1
    lines = result.stdout.splitlines()
    width = int(lines[0])
    height = int(lines[1])
    return width, height


def test_is_recording():
    """Test is_recording()."""
    recording = demo_dir.joinpath("021_day1234_测试录屏.mkv")
    timelapse = demo_dir.joinpath("022a_测试延时.mp4")
    nonexistent_file = demo_dir.joinpath("033_day111_nonexistent.mkv")
    assert recproc.is_recording(recording) is True
    assert recproc.is_recording(timelapse) is False
    assert recproc.is_recording(nonexistent_file) is False


def test_is_timelapse():
    """Test is_timelapse()."""
    recording = demo_dir.joinpath("021_day1234_测试录屏.mkv")
    timelapse = demo_dir.joinpath("022a_测试延时.mp4")
    nonexistent_file = demo_dir.joinpath("033_day111_nonexistent.mkv")
    assert recproc.is_timelapse(recording) is False
    assert recproc.is_timelapse(timelapse) is True
    assert recproc.is_timelapse(nonexistent_file) is False


def test_get_index():
    """Test get_index()."""
    recording = demo_dir.joinpath("021_day1234_测试录屏.mkv")
    timelapse = demo_dir.joinpath("022a_又一个测试延时.mp4")
    assert recproc.get_index(recording) == 21
    assert recproc.get_index(timelapse) == 22


def test_get_recordings():
    """Test get_recordings()."""
    recordings = recproc.get_recordings(demo_dir)
    recording_names = [r.name for r in recordings]
    assert "021_day1234_测试录屏.mkv" in recording_names
    assert "023_day4321_又一个测试录屏.mkv" in recording_names
    assert "098_day5555_不同格式的测试录屏.mp4" in recording_names


def test_get_timelapses():
    """Test get_timelapses()."""
    timelapses = recproc.get_timelapses(demo_dir)
    timelapse_names = [t.name for t in timelapses]
    assert "022a_测试延时.mp4" in timelapse_names
    assert "022a_又一个测试延时.mp4" in timelapse_names


def test_compress():
    """Test compress()."""
    in_file = demo_dir.joinpath("021_day1234_测试录屏.mkv")
    with tempfile.TemporaryDirectory() as temp_dir:
        out_file = Path(temp_dir).joinpath("tmp.mov")
        returncode = recproc.compress(in_file, out_file)
        in_file_duration = get_video_duration(in_file)
        out_file_duration = get_video_duration(out_file)
        out_file_width, out_file_height = get_video_resolution(out_file)
        assert returncode == 0
        assert in_file_duration == out_file_duration
        assert out_file_width == 1280
        assert out_file_height == 720


def test_compress_all():
    """Test compress_all()."""
    in_dir = demo_dir
    with tempfile.TemporaryDirectory() as temp_dir:
        out_dir = Path(temp_dir)
        recproc.compress_all(in_dir, out_dir)
        assert len(list(out_dir.iterdir())) == 3
    with tempfile.TemporaryDirectory() as temp_dir:
        out_dir = Path(temp_dir)
        recproc.compress_all(in_dir, out_dir, maxnum=1)
        assert len(list(out_dir.iterdir())) == 1


def test_read_extract_txt():
    """Test read_extract_txt()."""
    index, start, end, title = recproc.read_extract_txt(demo_dir, "extract.txt")
    assert index == [21, 23]
    assert start == ["00:00:00", "00:00:02"]
    assert end == ["00:00:01", "00:00:03"]
    assert title == ["第一秒片段", "第三秒片段"]


def test_extract():
    """Test extract()."""
    in_file = demo_dir.joinpath("021_day1234_测试录屏.mkv")
    with tempfile.TemporaryDirectory() as temp_dir:
        out_file = Path(temp_dir).joinpath("tmp.mov")
        returncode = recproc.extract(in_file, out_file, "00:00:01", "00:00:02")
        out_file_duration = get_video_duration(out_file)
        assert returncode == 0
        assert out_file_duration == 1.0


def test_get_extract_jobs():
    """Test get_extract_jobs()."""
    in_dir = demo_dir
    with tempfile.TemporaryDirectory() as temp_dir:
        out_dir = Path(temp_dir)
        in_files, out_files, start, end = recproc.get_extract_jobs(in_dir, out_dir)
        assert in_files[0] == in_dir.joinpath("021_day1234_测试录屏.mkv")
        assert in_files[1] == in_dir.joinpath("023_day4321_又一个测试录屏.mkv")
        assert out_files[0] == out_dir.joinpath("clip_021_第一秒片段.mp4")
        assert out_files[1] == out_dir.joinpath("clip_023_第三秒片段.mp4")
        assert start == ["00:00:00", "00:00:02"]
        assert end == ["00:00:01", "00:00:03"]


def test_extract_all():
    """Test extract_all()."""
    in_dir = demo_dir
    with tempfile.TemporaryDirectory() as temp_dir:
        out_dir = Path(temp_dir)
        recproc.extract_all(in_dir, out_dir)
        assert len(list(out_dir.iterdir())) == 2
    with tempfile.TemporaryDirectory() as temp_dir:
        out_dir = Path(temp_dir)
        recproc.extract_all(in_dir, out_dir, maxnum=1)
        assert len(list(out_dir.iterdir())) == 1
