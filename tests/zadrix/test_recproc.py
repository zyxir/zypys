"""compress.py 的單元測試。"""

import logging
import unittest

from zypys.zadrix.recproc import RecordProcessor


class Test(unittest.TestCase):
    """此文件的单元測試。"""

    def test_records(self):
        """測試錄像讀取功能。"""
        srcdir = "E:\\zadrix-records\\300days"
        targetdir = "E:\\zadrix-records\\300days_archive"
        processor = RecordProcessor(srcdir, targetdir)
        print(processor)

    def test_compress(self):
        """測試䤸像壓縮功能。"""
        logging.disable(logging.CRITICAL)
        srcdir = "E:\\zadrix-records\\300days"
        targetdir = "E:\\zadrix-records\\300days_archive"
        processor = RecordProcessor(srcdir, targetdir)
        logging.disable(logging.NOTSET)
        processor.compress(2)

    def test_extract(self):
        """測試䤸像提取功能。"""
        logging.disable(logging.CRITICAL)
        srcdir = "E:\\zadrix-records\\300days"
        targetdir = "E:\\zadrix-records\\300days_archive"
        processor = RecordProcessor(srcdir, targetdir)
        logging.disable(logging.NOTSET)
        processor.extract(2)

    def test_copy_timelapses(self):
        """測試延時攝影拷貝功能。"""
        logging.disable(logging.CRITICAL)
        srcdir = "E:\\zadrix-records\\300days"
        targetdir = "E:\\zadrix-records\\300days_archive"
        processor = RecordProcessor(srcdir, targetdir)
        logging.disable(logging.NOTSET)
        processor.copy_timelapses()


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    unittest.main()
