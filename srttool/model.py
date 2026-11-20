"""SRT 字幕的数据模型与时间戳工具。"""

from __future__ import annotations

import re
from dataclasses import dataclass, replace

_TIMESTAMP_RE = re.compile(r"^(\d{1,3}):([0-5]\d):([0-5]\d)[,.](\d{3})$")


def parse_timestamp(value: str) -> int:
    """把 ``HH:MM:SS,mmm`` 转换成毫秒。

    Raises:
        TypeError: value 不是字符串。
        ValueError: 时间戳格式不合法。
    """
    if not isinstance(value, str):
        raise TypeError("时间戳必须是字符串")
    match = _TIMESTAMP_RE.match(value.strip())
    if match is None:
        raise ValueError("非法时间戳: {0!r}".format(value))
    hours, minutes, seconds, millis = (int(part) for part in match.groups())
    return ((hours * 60 + minutes) * 60 + seconds) * 1000 + millis


def format_timestamp(milliseconds: int, separator: str = ",") -> str:
    """把毫秒转换成 ``HH:MM:SS,mmm``，负数按 0 处理。"""
    if milliseconds < 0:
        milliseconds = 0
    hours, remainder = divmod(milliseconds, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    seconds, millis = divmod(remainder, 1000)
    return "{0:02d}:{1:02d}:{2:02d}{3}{4:03d}".format(
        hours, minutes, seconds, separator, millis
    )


@dataclass(frozen=True)
class Cue:
    """一条字幕。"""

    index: int
    start_ms: int
    end_ms: int
    text: str

    @property
    def duration_ms(self) -> int:
        return self.end_ms - self.start_ms

    def with_times(self, start_ms: int, end_ms: int) -> "Cue":
        return replace(self, start_ms=start_ms, end_ms=end_ms)
