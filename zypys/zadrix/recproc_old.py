"""此腳本用於按一定標準來壓縮我的生存錄像。

其優勢有：

1. 壓縮參數在腳本中已定義好，無需重複輸入。
2. 可以一次轉換一個文件夾的視頻，並且會自動跳過已轉換完成的視頻。
"""

import argparse
import csv
import datetime
import logging
import os
import re
import shutil
import subprocess


class RecordProcessor:
    """䤸像處理器類。"""

    # 符合該正則表達式的視頻才會被認爲是生存原始錄像。
    RE_RECORD = re.compile("^[0-9]+_day[0-9]+_.*\\.(mp4|mov|mkv)$")

    # 用於提取錄像編號的正則表達式。
    RE_INDEX = re.compile("^([0-9]+).*$")

    # 符合該正則表達式的視頻才會被認爲是延時視頻。
    RE_TIMELAPSE = re.compile("^[0-9]+[a-z]+_.*\\.(mp4|mov|mkv)")

    # 默認的壓縮命令。
    CMD_COMPRESS = "ffmpeg -i {input} -loglevel warning" + \
        " -preset medium -c:v libx265 -crf 28 " + \
        " -s 1280x720 -filter:v fps=30" + \
        " {output}"

    # 默認的提取命令。
    CMD_EXTRACT = "ffmpeg -i {input} -loglevel warning" + \
        " -preset medium -c:v libx264 -crf 18 " + \
        " -x264-params keyint=30" + \
        " -ss {start} -to {end}" + \
        " {output}"

    # 提取所參考的文件名。
    EXTRACT_TXT = "extract.txt"

    def __init__(self, srcdir: str, targetdir: str):
        """初始化䤸像處理器。"""
        # 提取所有錄像文件之信息。

        self.srcdir = srcdir
        self.indices = []  # 文件編號。
        indexlens = []  # 文件編號數字之位數。
        self.fnames = []  # 僅文件名。
        self.files = []  # 絕對路徑。
        self.timelapses = []  # 延時攝影文件。
        logging.info('Start searching for record files.')
        try:
            for f in os.scandir(srcdir):
                if f.is_file() and self.RE_RECORD.fullmatch(f.name):
                    logging.debug('Record found: "%s".', f.name)
                    self.files.append(os.path.abspath(f.path))
                    self.fnames.append(f.name)
                    index_str = self.RE_INDEX.search(f.name).group(1)
                    self.indices.append(int(index_str))
                    indexlens.append(len(index_str))
                elif f.is_file() and self.RE_TIMELAPSE.fullmatch(f.name):
                    logging.debug('Timelapse found: "%s"', f.name)
                    self.timelapses.append(os.path.abspath(f.path))
            self.num = len(self.files)  # 找到的錄像文件數量。
            self.index_maxlen = max(indexlens)  # 最長的編號位數，僅用於打印。
            logging.info('Searching complete, %d records found.', self.num)
        except FileNotFoundError:
            raise FileNotFoundError('Source directory not found.')

        # 對所有䤸像文件按照編號排序。

        zipped = zip(self.files, self.fnames, self.indices)
        zipped = sorted(zipped, key=lambda pair: pair[2])
        for i, elem in enumerate(zipped):
            self.files[i] = elem[0]
            self.fnames[i] = elem[1]
            self.indices[i] = elem[2]
        logging.info('Records reordered.')

        # 檢查目標目䤸是否存在。如不存在，則嘗試創建之。

        if not os.path.isdir(targetdir):
            os.mkdir(targetdir)
            logging.info(
                'Target directory "%s" has been created.', targetdir
            )
        self.targetdir = targetdir

    def __iter__(self):
        """此類的迭代器。"""
        i = 0
        while i < self.num:
            yield (self.indices[i], self.fnames[i], self.files[i])
            i = i + 1

    def __str__(self):
        """此類的字符串表示。"""
        self_str = '- Records in "%s":\n  {\n' % self.srcdir
        for index, fname, _ in self:
            index_str = str(index)
            self_str += '    %s:' % index_str
            number_of_spaces = self.index_maxlen + 1 - len(index_str)
            self_str += ' ' * number_of_spaces
            self_str += '"%s",\n' % fname
        self_str += '  }\n'
        self_str += '- Timelapses in "%s":\n  {\n' % self.srcdir
        for timelapse in self.timelapses:
            self_str += '    %s,\n' % os.path.basename(timelapse)
        self_str += '  }'
        return self_str

    def compress(self, maxnum: int = 0):
        """將壓縮後的䤸像放入目標文件夹。

        最多壓縮 `maxnum` 個䤸像。當 `maxnum` 爲默認値 0 時，壓縮全部䤸像。
        """
        if maxnum == 0:
            maxnum = self.num
        for i, (_, fname, file) in enumerate(self):
            if i >= maxnum:
                break

            # 壓縮單個文件。接受被 Ctrl-C 打斷。

            try:
                now = datetime.datetime.now().strftime("%H:%M")
                logging.info(
                    '---- <%s> Start compressing "%s" [%d/%d] ----',
                    now, fname, i+1, maxnum
                )
                new_file = os.path.join(self.targetdir, fname)
                if os.path.isfile(new_file):
                    logging.info('Target file exists.')
                    continue
                cmd = self.CMD_COMPRESS.format(input=file, output=new_file)
                logging.info(cmd)
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.stderr is not None:
                    for line in result.stderr.splitlines():
                        logging.warning(line)
            except KeyboardInterrupt:
                logging.info('Compressing interrupted.')
                if 'new_file' in locals():
                    os.remove(new_file)
                break

    def extract(self, maxnum: int = 0):
        """將提取後的䤸像放入目標文件夾。

        提取依照的是源文件夾中的 EXTRACT_TXT 文件的内容。該文件由多行組成，每行
        之內容爲：

        INDEX START END TITLE

        意爲將編號爲 INDEX 的䤸像中由時間戳 START 開始、由時間戳 END 結束的一段
        給提取出來，並存入目標文件夾中。被提取的文件的全名將爲：

        clips_FULLINDEX_TITLE.mov

        其中，FULLINDEX 爲補零後的 INDEX。文件將被存爲 .mov 格式，最適合剪輯。

        EXTRACT_TXT 文件本身也會被複製到新文件夾中。
        """
        # 提取 EXTRACT_TXT 文件。

        extract_txt = os.path.join(self.srcdir, self.EXTRACT_TXT)
        with open(extract_txt, newline='', encoding='utf-8') as f:
            reader = csv.reader(f, delimiter=' ')
            data = list(reader)

        # 將 EXTRACT_TXT 本身複製到新文件夾。

        target_extract_txt = os.path.join(self.targetdir, self.EXTRACT_TXT)
        if not os.path.exists(target_extract_txt):
            shutil.copy(extract_txt, self.targetdir)
            logging.info(
                '%s has been copied to the target directory.'
                % self.EXTRACT_TXT
            )

        # 依次進行提取任務。

        if maxnum == 0:
            maxnum = len(data)
        for i in range(len(data)):
            if i > maxnum:
                break

            # 壓縮單個文件。接受被 Ctrl-C 打斷。

            try:
                now = datetime.datetime.now().strftime("%H:%M")
                index = int(data[i][0])
                start = data[i][1]
                end = data[i][2]
                title = data[i][3]
                logging.info(
                    '---- <%s> Start extracting "%s" [%d/%d] ----',
                    now, title, i+1, maxnum
                )

                # 寻找對應編號的䤸像是否存在。

                try:
                    record_subscript = self.indices.index(index)
                except ValueError:
                    logging.info('Source video not found.')
                    continue

                # 進行提取任務。

                file = self.files[record_subscript]
                fullindex_fmt = '%%0%dd' % self.index_maxlen
                fullindex_str = fullindex_fmt % index
                new_fname = 'clips_%s_%s.mov' % (fullindex_str, title)
                new_file = os.path.join(self.targetdir, new_fname)
                if os.path.isfile(new_file):
                    logging.info('Target file exists.')
                    continue
                cmd = self.CMD_EXTRACT.format(
                    input=file, start=start, end=end, output=new_file,
                )
                logging.info(cmd)
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.stderr is not None:
                    for line in result.stderr.splitlines():
                        logging.warning(line)
            except KeyboardInterrupt:
                logging.info('Extracting interrupted.')
                if 'new_file' in locals():
                    os.remove(new_file)
                break

    def copy_timelapses(self):
        """將所有延時攝影文件拷貝到目標文件夾中。"""
        targetdir_contents = os.listdir(self.targetdir)
        for timelapse in self.timelapses:
            basename = os.path.basename(timelapse)
            if basename not in targetdir_contents:
                shutil.copy(timelapse, self.targetdir)
                logging.info('"%s" copied.', basename)


def main():
    """此包的命令行界面。"""
    # 參數解析與較驗。

    parser = argparse.ArgumentParser(
        description="生存䤸像處理工具。"
    )
    parser.add_argument('srcdir', type=str, help='源文件夹。')
    parser.add_argument('-n', '--number', type=int, default=0, dest='number',
                        help='需要處理的視頻數量。')
    args = parser.parse_args()

    # 執行功能。

    logging.basicConfig(level=logging.INFO)
    srcdir = args.srcdir
    targetdir = os.path.join(
        os.path.dirname(srcdir),
        os.path.basename(os.path.abspath(srcdir)) + '_archive'
    )
    processor = RecordProcessor(srcdir, targetdir)
    processor.copy_timelapses()
    processor.compress(maxnum=args.number)
    try:
        processor.extract(maxnum=args.number)
    except FileNotFoundError:
        pass


if __name__ == '__main__':
    main()
