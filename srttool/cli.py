"""srttool 命令行入口。"""

from __future__ import annotations

import argparse
import sys
from typing import Optional, Sequence

from srttool.ops import OperationError, check_cues, scale_cues, shift_cues, to_vtt
from srttool.parser import SrtFormatError, format_srt, parse_srt


class InputError(Exception):
    """文件读写失败。"""


def read_text(path: str) -> str:
    """读取字幕文件；``-`` 表示标准输入。"""
    if path == "-":
        return sys.stdin.read()
    try:
        with open(path, "r", encoding="utf-8-sig") as handle:
            return handle.read()
    except FileNotFoundError as exc:
        raise InputError("文件不存在: {0}".format(path)) from exc
    except IsADirectoryError as exc:
        raise InputError("这是一个目录，不是文件: {0}".format(path)) from exc
    except PermissionError as exc:
        raise InputError("没有权限读取: {0}".format(path)) from exc
    except UnicodeDecodeError as exc:
        raise InputError("不是 UTF-8 文本: {0}".format(path)) from exc
    except OSError as exc:
        raise InputError(
            "读取失败: {0} ({1})".format(path, exc.strerror or exc)
        ) from exc


def write_text(path: str, content: str) -> None:
    """写入字幕文件；``-`` 表示标准输出。"""
    if path == "-":
        sys.stdout.write(content)
        return
    try:
        with open(path, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(content)
    except PermissionError as exc:
        raise InputError("没有写入权限: {0}".format(path)) from exc
    except OSError as exc:
        raise InputError(
            "写入失败: {0} ({1})".format(path, exc.strerror or exc)
        ) from exc


def _add_output_args(parser: argparse.ArgumentParser) -> None:
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "-o", "--output", metavar="OUT", default="-",
        help="输出文件，默认写入标准输出",
    )
    group.add_argument(
        "-i", "--in-place", action="store_true", help="直接覆盖原文件"
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="srttool",
        description="SRT 字幕时间轴工具：体检、平移、变速、转 WebVTT。",
    )
    subparsers = parser.add_subparsers(dest="command", required=True, metavar="COMMAND")

    check = subparsers.add_parser("check", help="检查序号、零时长、时间重叠等问题")
    check.add_argument("file", metavar="FILE", help="SRT 文件，- 表示标准输入")

    shift = subparsers.add_parser("shift", help="整体平移时间轴")
    shift.add_argument("file", metavar="FILE", help="SRT 文件，- 表示标准输入")
    shift.add_argument(
        "-s", "--seconds", type=float, required=True, metavar="SEC",
        help="平移秒数，正数延后、负数提前",
    )
    _add_output_args(shift)

    speed = subparsers.add_parser("speed", help="按倍速缩放时间轴")
    speed.add_argument("file", metavar="FILE", help="SRT 文件，- 表示标准输入")
    speed.add_argument(
        "-r", "--rate", type=float, required=True, metavar="RATE",
        help="倍速，例如 1.25 表示 1.25 倍速",
    )
    _add_output_args(speed)

    vtt = subparsers.add_parser("to-vtt", help="转换为 WebVTT")
    vtt.add_argument("file", metavar="FILE", help="SRT 文件，- 表示标准输入")
    vtt.add_argument(
        "-o", "--output", metavar="OUT", default="-",
        help="输出文件，默认写入标准输出",
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    in_place = bool(getattr(args, "in_place", False))
    if in_place and args.file == "-":
        print("错误: --in-place 不能用于标准输入", file=sys.stderr)
        return 2

    try:
        cues = parse_srt(read_text(args.file))
    except (InputError, SrtFormatError) as exc:
        print("错误: {0}".format(exc), file=sys.stderr)
        return 2

    if args.command == "check":
        issues = check_cues(cues)
        if issues:
            for issue in issues:
                print("- {0}".format(issue))
            print("\n共 {0} 条字幕，发现 {1} 个问题".format(len(cues), len(issues)))
            return 1
        print("共 {0} 条字幕，未发现问题".format(len(cues)))
        return 0

    try:
        if args.command == "shift":
            result = shift_cues(cues, args.seconds)
            output = format_srt(result.cues)
            summary = "已平移 {0} 条字幕".format(len(result.cues))
            if result.dropped:
                summary += "，丢弃 {0} 条".format(result.dropped)
            if result.clamped:
                summary += "，裁剪 {0} 条".format(result.clamped)
        elif args.command == "speed":
            scaled = scale_cues(cues, args.rate)
            output = format_srt(scaled)
            summary = "已按 {0:g} 倍速缩放 {1} 条字幕".format(
                float(args.rate), len(scaled)
            )
        else:
            output = to_vtt(cues)
            summary = "已转换 {0} 条字幕为 WebVTT".format(len(cues))
    except OperationError as exc:
        print("错误: {0}".format(exc), file=sys.stderr)
        return 2

    destination = args.file if in_place else getattr(args, "output", "-")
    try:
        write_text(destination, output)
    except InputError as exc:
        print("错误: {0}".format(exc), file=sys.stderr)
        return 2

    if destination == "-":
        print(summary, file=sys.stderr)
    else:
        print("{0} -> {1}".format(summary, destination), file=sys.stderr)
    return 0
