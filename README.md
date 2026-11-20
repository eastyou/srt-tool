# srt-tool

[![CI](https://github.com/eastyou/srt-tool/actions/workflows/ci.yml/badge.svg)](https://github.com/eastyou/srt-tool/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.9%2B-brightgreen.svg)](pyproject.toml)

SRT 字幕时间轴工具：体检、整体平移、按倍速缩放、转换为 WebVTT。

剪辑视频时经常遇到字幕整体快了几秒、换了片头片尾需要平移、或者要调整播放倍速。图形软件操作繁琐，这个命令行工具一行命令就能完成，并且会自动处理被推到 0 秒之前的字幕。

## 特性

- `check`：检查序号错误、零时长、时间重叠、空文本
- `shift`：整体平移时间轴，支持负数；越界的字幕自动裁剪或丢弃并给出统计
- `speed`：按倍速缩放时间轴，例如 `1.25` 表示 1.25 倍速
- `to-vtt`：SRT 转 WebVTT，时间戳改用 `.` 分隔
- 支持标准输入/输出与 `--in-place`，方便串联到脚本
- 严格校验格式，出错时指出第几段有问题
- 零依赖，Python 3.9+

## 安装

```bash
pip install "git+https://github.com/eastyou/srt-tool.git"
```

本地使用：

```bash
git clone https://github.com/eastyou/srt-tool.git
cd srt-tool
python3 -m pip install -e .
```

不安装也可以：`python3 -m srttool check demo.srt`

## 使用

```console
$ srttool check ep01.srt
- 第 3 条与第 4 条字幕时间重叠
- 第 7 条字幕文本为空

共 42 条字幕，发现 2 个问题
```

```bash
# 整体提前 1.5 秒，输出到新文件
srttool shift ep01.srt -s -1.5 -o ep01.fixed.srt

# 整体延后 2 秒，直接覆盖原文件
srttool shift ep01.srt -s 2 --in-place

# 按 1.25 倍速缩放（配合 1.25 倍速播放的视频）
srttool speed ep01.srt -r 1.25 -o ep01.fast.srt

# 转换为 WebVTT
srttool to-vtt ep01.srt -o ep01.vtt

# 从标准输入读取
cat ep01.srt | srttool check -
```

### 命令

| 命令 | 说明 |
| --- | --- |
| `srttool check FILE` | 检查字幕问题，有问题时退出码为 1 |
| `srttool shift FILE -s SEC [-o OUT \| -i]` | 平移时间轴，秒数可为负 |
| `srttool speed FILE -r RATE [-o OUT \| -i]` | 按倍速缩放时间轴 |
| `srttool to-vtt FILE [-o OUT]` | 转换为 WebVTT |

`-` 表示标准输入或标准输出，`-o` 省略时输出到标准输出，`-i/--in-place` 直接覆盖原文件。

### 平移规则

| 情况 | 处理方式 |
| --- | --- |
| 平移后开始时间 < 0，结束时间 > 0 | 开始时间裁剪为 0，计入"裁剪" |
| 平移后结束时间 ≤ 0 | 整条丢弃，计入"丢弃" |
| 其它 | 正常平移 |

平移与变速后会从 1 开始重新编号，保证序号连续。

### 退出码

| 退出码 | 含义 |
| --- | --- |
| `0` | 成功，或 `check` 未发现问题 |
| `1` | `check` 发现问题 |
| `2` | 参数错误、文件无法读取或字幕格式错误 |

## 作为库使用

```python
from srttool import parse_srt, format_srt, shift_cues, to_vtt

with open("demo.srt", encoding="utf-8") as handle:
    cues = parse_srt(handle.read())

result = shift_cues(cues, -1.5)
print(result.dropped, result.clamped)
print(format_srt(result.cues))
print(to_vtt(result.cues))
```

## 开发与测试

```bash
python3 -m unittest discover -s tests -v
```

CI 在 Python 3.9 ~ 3.13 上运行全部测试。

## License

[MIT](LICENSE) © 2026 eastyou
