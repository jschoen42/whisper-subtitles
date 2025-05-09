"""
    © Jürgen Schoenemeyer, 01.03.2025 17:52

    PUBLIC:
     - import_caption(dirname: Path | str, basename: str) -> Captions | None
     - writefile_srt(data_captions: List[Segment], dirname: Path | str, basename: str) -> None
     - writefile_vtt(data_captions: List[Segment], dirname: Path | str, basename: str) -> None
     - export_srt(captions: List[Segment], fps: float = 30) -> str
     - export_vtt(captions: List[Segment], fps: float = 30) -> str

    HELPER:
     - seconds_to_timecode_srt(x: float, fps: float) -> str
     - seconds_to_timecode_vtt(x: float, fps: float) -> str
     - parse_timecode(text: str) -> float
"""
from __future__ import annotations

from pathlib import Path
from typing import List, Tuple, TypedDict

import webvtt  # type: ignore[import-untyped]

from utils.file import export_text
from utils.trace import Trace
from utils.util import format_timestamp

# PUBLIC

class Segment(TypedDict):
    section: int
    start:   float
    end:     float
    text:    str

Captions = Tuple[
    List[Segment],
    int,
    List[int],
]

def import_caption(dirname: Path | str, basename: str) -> Captions | None:
    dirname = Path(dirname)

    filepath = dirname / basename
    extension = filepath.suffix

    if extension == ".vtt":
        try:
            captions = webvtt.read(filepath.as_posix())
        except OSError as error:
            Trace.error(f"[import_caption] {basename}: {error}")
            return None

    elif extension == ".srt":
        try:
            captions = webvtt.from_srt(filepath.as_posix())
        except OSError as error:
            Trace.error(f"[import_caption] {basename}: {error}")
            return None
    else:
        Trace.error(f"unknown extension '{extension}'")
        return None

    segments:  List[Segment] = []
    words:     int = 0
    line_type: List[int] = [0, 0]

    for i, caption in enumerate(captions.captions):
        start = parse_timecode(caption.start)
        end   = parse_timecode(caption.end)
        text  = str(caption.text)

        tmp = text.replace("\n", " ")
        words += len(tmp.split(" "))

        if "\n" in text:
            line_type[1] += 1
        else:
            line_type[0] += 1

        segment: Segment = {
            "section": i + 1,
            "start": start,
            "end":   end,
            "text":  text,
        }

        segments.append(segment)

    return segments, words, line_type

def writefile_srt(data_captions: List[Segment], dirname: Path | str, basename: str) -> None:
    export_text(dirname, basename, export_srt(data_captions, 30), newline = "\r\n")

def writefile_vtt(data_captions: List[Segment], dirname: Path | str, basename: str) -> None:
    export_text(dirname, basename, export_vtt(data_captions, 30 ), newline = "\r\n")

def export_srt(captions: List[Segment], fps: float = 30) -> str:
    text = ""

    for caption in captions:
        start = seconds_to_timecode_srt(caption["start"], fps)
        end   = seconds_to_timecode_srt(caption["end"], fps)

        text += str(caption["section"]) + "\n"
        text += start + " --> " + end + "\n"
        text += caption["text"] + "\n"
        text += "\n"

    return text

def export_vtt(captions: List[Segment], fps: float = 30) -> str:
    text = "WEBVTT\n\n"

    for caption in captions:
        start = seconds_to_timecode_vtt(caption["start"], fps)
        end   = seconds_to_timecode_vtt(caption["end"], fps)

        text += start + " --> " + end + "\n"
        text += caption["text"] + "\n"
        text += "\n"

    return text

# HELPER
def seconds_to_timecode_srt(x: float, fps: float = 30) -> str:
    # srt: 00:01:06,680
    return format_timestamp(x, always_include_hours=True, decimal_marker=",", fps=fps)

def seconds_to_timecode_vtt(x: float, fps: float = 30) -> str:
    # vtt: 00:01:06.680
    return format_timestamp(x, always_include_hours=True, decimal_marker=".", fps=fps)

def parse_timecode(text: str) -> float:
    tmp = text.replace(",", ".").split(":")

    h = int(tmp[0])
    m = int(tmp[1])
    s = float(tmp[2])

    return h * 3600 + m * 60 + s
