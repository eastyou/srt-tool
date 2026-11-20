"""srttool: SRT 字幕时间轴工具。"""

from srttool.model import Cue, format_timestamp, parse_timestamp
from srttool.ops import check_cues, scale_cues, shift_cues, to_vtt
from srttool.parser import SrtFormatError, format_srt, parse_srt

__all__ = [
    "Cue",
    "SrtFormatError",
    "check_cues",
    "format_srt",
    "format_timestamp",
    "parse_srt",
    "parse_timestamp",
    "scale_cues",
    "shift_cues",
    "to_vtt",
]
__version__ = "0.1.0"
