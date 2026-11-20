"""字幕时间轴操作：平移、变速、转 VTT、体检。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Sequence

from srttool.model import Cue, format_timestamp

MAX_RATE = 100.0


class OperationError(ValueError):
    """操作参数不合法。"""


@dataclass(frozen=True)
class ShiftResult:
    cues: List[Cue]
    dropped: int
    clamped: int


def shift_cues(cues: Sequence[Cue], seconds: float) -> ShiftResult:
    """整体平移字幕。

    开始时间被推到 0 之前但结束时间仍为正时，会裁剪到 0；
    整条字幕都落在 0 之前时直接丢弃。

    Raises:
        TypeError: seconds 不是数字。
        OperationError: seconds 不是有限数。
    """
    if isinstance(seconds, bool) or not isinstance(seconds, (int, float)):
        raise TypeError("seconds 必须是数字")
    if seconds != seconds or seconds in (float("inf"), float("-inf")):
        raise OperationError("seconds 必须是有限数")

    delta = int(round(float(seconds) * 1000))
    shifted: List[Cue] = []
    dropped = 0
    clamped = 0
    for cue in cues:
        start_ms = cue.start_ms + delta
        end_ms = cue.end_ms + delta
        if end_ms <= 0:
            dropped += 1
            continue
        if start_ms < 0:
            start_ms = 0
            clamped += 1
        shifted.append(cue.with_times(start_ms, end_ms))
    return ShiftResult(cues=shifted, dropped=dropped, clamped=clamped)


def scale_cues(cues: Sequence[Cue], rate: float) -> List[Cue]:
    """按倍速缩放时间轴，``rate=1.25`` 表示 1.25 倍速（时长变短）。

    Raises:
        TypeError: rate 不是数字。
        OperationError: rate 不在 (0, 100] 范围内。
    """
    if isinstance(rate, bool) or not isinstance(rate, (int, float)):
        raise TypeError("rate 必须是数字")
    if rate != rate:
        raise OperationError("倍速必须是有效数字")
    if rate <= 0:
        raise OperationError("倍速必须大于 0")
    if rate > MAX_RATE:
        raise OperationError("倍速不能超过 {0:g}".format(MAX_RATE))

    factor = float(rate)
    return [
        cue.with_times(
            int(round(cue.start_ms / factor)),
            int(round(cue.end_ms / factor)),
        )
        for cue in cues
    ]


def to_vtt(cues: Sequence[Cue]) -> str:
    """转换为 WebVTT 文本。"""
    lines: List[str] = ["WEBVTT", ""]
    for cue in cues:
        lines.append(
            "{0} --> {1}".format(
                format_timestamp(cue.start_ms, "."),
                format_timestamp(cue.end_ms, "."),
            )
        )
        lines.append(cue.text)
        lines.append("")
    return "\n".join(lines)


def check_cues(cues: Sequence[Cue]) -> List[str]:
    """检查字幕中的常见问题，返回人类可读的问题列表。"""
    issues: List[str] = []
    if not cues:
        return ["字幕为空"]

    for position, cue in enumerate(cues, start=1):
        if cue.index != position:
            issues.append(
                "第 {0} 条字幕序号为 {1}，与顺序不一致".format(position, cue.index)
            )
        if cue.duration_ms <= 0:
            issues.append(
                "第 {0} 条字幕时长不为正（{1}）".format(
                    position, format_timestamp(cue.start_ms)
                )
            )
        if not cue.text.strip():
            issues.append("第 {0} 条字幕文本为空".format(position))
        if position > 1:
            previous = cues[position - 2]
            if cue.start_ms < previous.end_ms:
                issues.append(
                    "第 {0} 条与第 {1} 条字幕时间重叠".format(position - 1, position)
                )
    return issues
