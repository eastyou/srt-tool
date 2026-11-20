"""时间轴操作与体检的单元测试。"""

import unittest

from srttool.model import Cue
from srttool.ops import OperationError, check_cues, scale_cues, shift_cues, to_vtt


def make_cue(index, start, end, text="文本"):
    return Cue(index=index, start_ms=start, end_ms=end, text=text)


class ShiftTests(unittest.TestCase):
    def test_positive_shift(self):
        cues = [make_cue(1, 1000, 2000)]
        result = shift_cues(cues, 1.5)
        self.assertEqual(result.cues[0].start_ms, 2500)
        self.assertEqual(result.cues[0].end_ms, 3500)
        self.assertEqual(result.dropped, 0)
        self.assertEqual(result.clamped, 0)

    def test_negative_shift_drops_and_clamps(self):
        cues = [make_cue(1, 1000, 3500), make_cue(2, 4000, 6000)]
        result = shift_cues(cues, -5)
        self.assertEqual(result.dropped, 1)
        self.assertEqual(result.clamped, 1)
        self.assertEqual(len(result.cues), 1)
        self.assertEqual(result.cues[0].start_ms, 0)
        self.assertEqual(result.cues[0].end_ms, 1000)

    def test_empty_input(self):
        result = shift_cues([], 2.0)
        self.assertEqual(result.cues, [])
        self.assertEqual(result.dropped, 0)

    def test_invalid_seconds(self):
        with self.assertRaises(TypeError):
            shift_cues([], "1")
        with self.assertRaises(TypeError):
            shift_cues([], True)
        with self.assertRaises(OperationError):
            shift_cues([], float("nan"))
        with self.assertRaises(OperationError):
            shift_cues([], float("inf"))


class ScaleTests(unittest.TestCase):
    def test_double_speed(self):
        cues = [make_cue(1, 1000, 3000)]
        scaled = scale_cues(cues, 2)
        self.assertEqual(scaled[0].start_ms, 500)
        self.assertEqual(scaled[0].end_ms, 1500)

    def test_slow_down(self):
        cues = [make_cue(1, 1000, 2000)]
        scaled = scale_cues(cues, 0.5)
        self.assertEqual(scaled[0].start_ms, 2000)
        self.assertEqual(scaled[0].end_ms, 4000)

    def test_invalid_rate(self):
        for rate in (0, -1, 101):
            with self.assertRaises(OperationError):
                scale_cues([], rate)
        with self.assertRaises(OperationError):
            scale_cues([], float("nan"))
        with self.assertRaises(TypeError):
            scale_cues([], None)  # type: ignore[arg-type]


class VttTests(unittest.TestCase):
    def test_header_and_timestamps(self):
        text = to_vtt([make_cue(1, 1000, 2500, "第一句")])
        self.assertTrue(text.startswith("WEBVTT\n"))
        self.assertIn("00:00:01.000 --> 00:00:02.500", text)
        self.assertIn("第一句", text)


class CheckTests(unittest.TestCase):
    def test_empty_cues(self):
        self.assertEqual(check_cues([]), ["字幕为空"])

    def test_clean_cues(self):
        cues = [make_cue(1, 0, 1000), make_cue(2, 1000, 2000)]
        self.assertEqual(check_cues(cues), [])

    def test_overlap_and_zero_duration(self):
        cues = [make_cue(1, 0, 1000), make_cue(2, 900, 900)]
        issues = check_cues(cues)
        self.assertTrue(any("重叠" in issue for issue in issues))
        self.assertTrue(any("时长不为正" in issue for issue in issues))

    def test_index_mismatch(self):
        cues = [make_cue(1, 0, 1000), make_cue(5, 1000, 2000)]
        issues = check_cues(cues)
        self.assertTrue(any("序号" in issue for issue in issues))

    def test_empty_text(self):
        cues = [make_cue(1, 0, 1000, "   ")]
        self.assertTrue(any("文本为空" in issue for issue in check_cues(cues)))


if __name__ == "__main__":
    unittest.main()
