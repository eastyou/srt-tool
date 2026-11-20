"""srttool 命令行的单元测试。"""

import io
import os
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout

from srttool.cli import main
from srttool.parser import parse_srt

SAMPLE = (
    "1\n00:00:10,000 --> 00:00:12,000\n第一句\n\n"
    "2\n00:00:13,000 --> 00:00:15,000\n第二句\n"
)
OVERLAP = (
    "1\n00:00:10,000 --> 00:00:12,000\n第一句\n\n"
    "2\n00:00:11,000 --> 00:00:15,000\n第二句\n"
)


class CliTests(unittest.TestCase):
    def _run(self, argv):
        stdout = io.StringIO()
        stderr = io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            code = main(argv)
        return code, stdout.getvalue(), stderr.getvalue()

    def _make_file(self, directory, content):
        path = os.path.join(directory, "demo.srt")
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(content)
        return path

    def test_check_clean_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self._make_file(tmp, SAMPLE)
            code, out, _ = self._run(["check", path])
        self.assertEqual(code, 0)
        self.assertIn("未发现问题", out)

    def test_check_overlap_exits_one(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self._make_file(tmp, OVERLAP)
            code, out, _ = self._run(["check", path])
        self.assertEqual(code, 1)
        self.assertIn("重叠", out)

    def test_shift_writes_output_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self._make_file(tmp, SAMPLE)
            output = os.path.join(tmp, "out.srt")
            code, _, err = self._run(["shift", path, "-s", "1.5", "-o", output])
            with open(output, "r", encoding="utf-8") as handle:
                cues = parse_srt(handle.read())
        self.assertEqual(code, 0)
        self.assertEqual(cues[0].start_ms, 11500)
        self.assertIn("已平移", err)

    def test_shift_in_place(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self._make_file(tmp, SAMPLE)
            code, _, _ = self._run(["shift", path, "-s", "2", "--in-place"])
            with open(path, "r", encoding="utf-8") as handle:
                cues = parse_srt(handle.read())
        self.assertEqual(code, 0)
        self.assertEqual(cues[0].start_ms, 12000)

    def test_speed_to_stdout(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self._make_file(tmp, SAMPLE)
            code, out, err = self._run(["speed", path, "-r", "2"])
        self.assertEqual(code, 0)
        self.assertIn("00:00:05,000 --> 00:00:06,000", out)
        self.assertIn("2 倍速", err)

    def test_to_vtt(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self._make_file(tmp, SAMPLE)
            code, out, _ = self._run(["to-vtt", path])
        self.assertEqual(code, 0)
        self.assertTrue(out.startswith("WEBVTT"))

    def test_missing_file(self):
        code, _, err = self._run(["check", "/definitely/not/here.srt"])
        self.assertEqual(code, 2)
        self.assertIn("文件不存在", err)

    def test_invalid_format(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self._make_file(tmp, "这不是字幕")
            code, _, err = self._run(["check", path])
        self.assertEqual(code, 2)
        self.assertIn("错误", err)

    def test_invalid_rate(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self._make_file(tmp, SAMPLE)
            code, _, err = self._run(["speed", path, "-r", "0"])
        self.assertEqual(code, 2)
        self.assertIn("倍速必须大于 0", err)

    def test_in_place_with_stdin_is_rejected(self):
        code, _, err = self._run(["shift", "-", "-s", "1", "--in-place"])
        self.assertEqual(code, 2)
        self.assertIn("--in-place", err)


if __name__ == "__main__":
    unittest.main()
