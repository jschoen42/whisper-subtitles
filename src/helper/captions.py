"""
    © Jürgen Schoenemeyer, 04.01.2025

    PUBLIC:
     - second_to_timecode_srt(x: float, fps: float) -> str
     - seconds_to_timecode_vtt(x: float, fps: float) -> str
     - seconds_to_timecode_excel(x: float) -> str
     - parse_timecode(text: str) -> float
     - export_srt(captions: list[dict], fps: float = 30) -> str
     - export_vtt(captions: list[dict],  fps: float = 30) -> str
     - import_caption(dirname: Path|str, basename: str) -> None | Tuple[dict, int, list]
     - writefile_srt(data_captions: list, dirname: Path | str, basename: str)
     - writefile_vtt(data_captions: list, dirname: Path | str, basename: str)
"""

from pathlib import Path
from typing  import Any, Tuple

import webvtt

from utils.trace import Trace
from utils.util import export_text, format_timestamp

def second_to_timecode_srt(x: float, fps: float) -> str:
    return format_timestamp(x, always_include_hours=True, decimal_marker=",", fps=fps)

def seconds_to_timecode_vtt(x: float, fps: float) -> str:
    return format_timestamp(x, always_include_hours=True, decimal_marker=".", fps=fps)

def seconds_to_timecode_excel(x: float) -> str:
    return format_timestamp(x, always_include_hours=False, decimal_marker=".")

# vtt: 00:01:06.680
# srt: 00:01:06,680

def parse_timecode(text: str) -> float:
    tmp = text.replace(",", ".").split(":")

    h = int(tmp[0])
    m = int(tmp[1])
    s = float(tmp[2])

    return h * 3600 + m * 60 + s

def export_srt(captions: list[dict], fps: float = 30) -> str:
    text = ""

    for caption in captions:
        start = second_to_timecode_srt(caption["start"], fps)
        end   = second_to_timecode_srt(caption["end"], fps)

        text += str(caption["section"]) + "\n"
        text += start + " --> " + end + "\n"
        text += caption["text"] + "\n"
        text += "\n"

    return text

def export_vtt(captions: list[dict], fps: float = 30) -> str:
    text = "WEBVTT\n\n"

    for caption in captions:
        start = seconds_to_timecode_vtt(caption["start"], fps)
        end   = seconds_to_timecode_vtt(caption["end"], fps)

        text += start + " --> " + end + "\n"
        text += caption["text"] + "\n"
        text += "\n"

    return text

def import_caption(dirname: Path|str, basename: str) -> None | Tuple[dict, int, list]:
    filepath = Path(dirname, basename)

    extention = filepath.suffix
    if extention.lower() == ".vtt":
        ret = webvtt.read(str(filepath))
    elif extention.lower() == ".srt":
        try:
            ret = webvtt.from_srt(str(filepath))
        except OSError as error:
            Trace.error(f"[import_caption] {basename}: {error}")
            return None
    else:
        Trace.error(f"unknown extention '{extention}'")
        ret = None

    segments:  list[dict] = []
    words:     int = 0
    line_type: list = [0, 0]

    if ret:
        for i, caption in enumerate(ret):
            start = parse_timecode(caption.start)
            end   = parse_timecode(caption.end)
            text  = caption.text

            tmp = text.replace("\n", " ")
            words += len(tmp.split(" "))

            if "\n" in text:
                line_type[1] += 1
            else:
                line_type[0] += 1

            segment: dict[str, Any] = {}
            segment["section"] = i+1
            segment["start"]   = start
            segment["end"]     = end
            segment["text"]    = text

            segments.append(segment)

    return segments, words, line_type

def writefile_srt(data_captions: list, dirname: Path | str, basename: str) -> None:
    export_text(dirname, basename, export_srt(data_captions, 30), ret_lf = True)

def writefile_vtt(data_captions: list, dirname: Path | str, basename: str) -> None:
    export_text(dirname, basename, export_vtt(data_captions, 30 ), ret_lf = True)
