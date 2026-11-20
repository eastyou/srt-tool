"""SRT 解析与生成的单元测试。"""

import unittest

from srttool.model import format_timestamp, parse_timestamp
from srttool.parser import SrtFormatError, format_srt, parse_srt

SAMPLE = (
    "1\n00:00:01,000 --> 00:00:03,500\n第一句\n\n"
    "2\n00:00:04,000 --> 00:00:06,000\n第二句\n第二行\n"
)


class TimestampTests(unittest.TestCase):
    def test_parse(self):
        self.assertEqual(parse_timestamp("00:00:00,000"), 0)
        self.assertEqual(parse_timestamp("00:00:01,500"), 1500)
        self.assertEqual(parse_timestamp("01:02:03,004"), 3_723_004)

    def test_parse_accepts_dot_separator(self):
        self.assertEqual(parse_timestamp("00:00:01.500"), 1500)

    def test_invalid_timestamp(self):
        for value in ("1:2:3", "00:61:00,000", "abc", ""):
            with self.assertRaises(ValueError):
                parse_timestamp(value)

    def test_non_string_timestamp(self):
        with self.assertRaises(TypeError):
            parse_timestamp(1000)  # type: ignore[arg-type]

    def test_format(self):
        self.assertEqual(format_timestamp(0), "00:00:00,000")
        self.assertEqual(format_timestamp(3_723_004), "01:02:03,004")
        self.assertEqual(format_timestamp(1_500, "."), "00:00:01.500")

    def test_format_negative_clamps_to_zero(self):
        self.assertEqual(format_timestamp(-100), "00:00:00,000")


class ParseTests(unittest.TestCase):
    def test_parse_sample(self):
        cues = parse_srt(SAMPLE)
        self.assertEqual(len(cues), 2)
        self.assertEqual(cues[0].start_ms, 1000)
        self.assertEqual(cues[0].end_ms, 3500)
        self.assertEqual(cues[0].text, "第一句")
        self.assertEqual(cues[1].text, "第二句\n第二行")
        self.assertEqual(cues[1].duration_ms, 2000)

    def test_crlf_and_bom(self):
        content = "\ufeff1\r\n00:00:01,000 --> 00:00:02,000\r\n你好\r\n"
        cues = parse_srt(content)
        self.assertEqual(len(cues), 1)
        self.assertEqual(cues[0].text, "你好")

    def test_roundtrip(self):
        cues = parse_srt(SAMPLE)
        again = parse_srt(format_srt(cues))
        self.assertEqual(again, cues)

    def test_empty_content(self):
        with self.assertRaises(SrtFormatError):
            parse_srt("   \n\n")

    def test_non_string_content(self):
        with self.assertRaises(TypeError):
            parse_srt(None)  # type: ignore[arg-type]

    def test_missing_timeline(self):
        with self.assertRaises(SrtFormatError):
            parse_srt("1\n没有时间轴\n文本\n")

    def test_invalid_index(self):
        with self.assertRaises(SrtFormatError):
            parse_srt("一\n00:00:01,000 --> 00:00:02,000\n文本\n")

    def test_invalid_timeline(self):
        with self.assertRaises(SrtFormatError):
            parse_srt("1\n00:00:01 --> 00:00:02\n文本\n")

    def test_end_before_start(self):
        with self.assertRaises(SrtFormatError):
            parse_srt("1\n00:00:05,000 --> 00:00:01,000\n文本\n")

    def test_format_empty_list(self):
        self.assertEqual(format_srt([]), "")


if __name__ == "__main__":
    unittest.main()
