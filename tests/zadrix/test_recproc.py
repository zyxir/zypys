"""Unit tests of recproc.py

These tests apply functions in the module to a set of demo videos, trying to
validate the module as much as possible.
"""

from pathlib import Path

from zypys.zadrix import recproc

# The directory of demo videos.
demo_dir = Path("tests/zadrix/test_recproc_demo_videos")


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
