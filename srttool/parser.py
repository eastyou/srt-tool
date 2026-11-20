"""SRT 字幕解析与生成。"""

from __future__ import annotations

import re
from typing import List

from srttool.model import Cue, format_timestamp, parse_timestamp

_TIMELINE_RE = re.compile(r"^\s*(\S+)\s*-->\s*(\S+)(?:\s+.*)?$")
_BLOCK_SPLIT_RE = re.compile(r"\n[ \t]*\n+")


class SrtFormatError(ValueError):
    """字幕内容不符合 SRT 格式。"""


def parse_srt(content: str) -> List[Cue]:
    """解析 SRT 文本。

    Raises:
        TypeError: content 不是字符串。
        SrtFormatError: 内容为空或格式不合法。
    """
    if not isinstance(content, str):
        raise TypeError("content 必须是 str")

    normalized = content.replace("\r\n", "\n").replace("\r", "\n").lstrip("\ufeff")
    if not normalized.strip():
        raise SrtFormatError("字幕内容为空")

    cues: List[Cue] = []
    for block_number, block in enumerate(
        _BLOCK_SPLIT_RE.split(normalized.strip()), start=1
    ):
        lines = block.split("\n")
        if len(lines) < 2:
            raise SrtFormatError(
                "第 {0} 段缺少时间轴行".format(block_number)
            )

        index_text = lines[0].strip()
        if not index_text.isdigit():
            raise SrtFormatError(
                "第 {0} 段序号不是数字: {1!r}".format(block_number, index_text)
            )

        timeline = _TIMELINE_RE.match(lines[1].strip())
        if timeline is None:
            raise SrtFormatError(
                "第 {0} 段时间轴格式错误: {1!r}".format(block_number, lines[1].strip())
            )
        try:
            start_ms = parse_timestamp(timeline.group(1))
            end_ms = parse_timestamp(timeline.group(2))
        except ValueError as exc:
            raise SrtFormatError(
                "第 {0} 段时间戳非法: {1}".format(block_number, exc)
            ) from exc
        if end_ms < start_ms:
            raise SrtFormatError(
                "第 {0} 段结束时间早于开始时间".format(block_number)
            )

        cues.append(
            Cue(
                index=int(index_text),
                start_ms=start_ms,
                end_ms=end_ms,
                text="\n".join(lines[2:]),
            )
        )
    return cues


def format_srt(cues: List[Cue]) -> str:
    """生成 SRT 文本，序号从 1 开始重新编号。"""
    blocks: List[str] = []
    for position, cue in enumerate(cues, start=1):
        blocks.append(
            "{0}\n{1} --> {2}\n{3}".format(
                position,
                format_timestamp(cue.start_ms),
                format_timestamp(cue.end_ms),
                cue.text,
            )
        )
    if not blocks:
        return ""
    return "\n\n".join(blocks) + "\n"
