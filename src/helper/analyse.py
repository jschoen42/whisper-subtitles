"""
    © Jürgen Schoenemeyer, 30.03.2025 15:27

    src/helper/analyse.py

    PUBLIC:
     - analyse_results(model_id: str, model_name: str, media_type: str, media_name: str, media_path: str, json_path: str, _info_path: str, _analyse_path: str, beam_size: int) -> None | Dict:
     - show_parts_results(project: str, results: List[Dict]) -> Tuple[int, int]:
     - show_complete_results(project: str, duration: float, words: int) -> None
     - get_video_length(path: Path | str, filename: str) -> None | float
"""
from __future__ import annotations

import io

from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np

from utils.file import import_json
from utils.metadata import get_audio_duration, get_audio_metadata, get_video_metadata
from utils.trace import Trace

def analyse_results(model_id: str, model_name: str, media_type: str, media_name: str, media_path: Path | str, json_path: str, _info_path: str, _analyse_path: str, beam_size: int) -> None | Dict[str, Any]:

    media_path = Path(media_path)

    condition_on_previous_text = True
    if model_name == "large-v3":
        condition_on_previous_text = False

    media_pathname = media_path / (media_name + "." + media_type)
    filename     = f"{media_name} - ({model_id}) {model_name}"
    filename_two = f"{filename}-fast#{condition_on_previous_text}#beam-{beam_size}"

    media_duration = 0.0
    try:
        with media_pathname.open(mode="rb") as media_file:
            media_data = media_file.read()

            if media_type == "mp4":
                media_details = get_video_metadata(io.BytesIO(media_data))
                if media_details is None:
                    return None
                media_duration = media_details["duration"]

            elif media_type == "mp3":
                media_details = get_audio_metadata(io.BytesIO(media_data))
                if media_details is None:
                    return None
                media_duration = media_details["duration"]

            elif media_type == "wav":
                media_duration = get_audio_duration(io.BytesIO(media_data))

            else:
                Trace.fatal(f"unsupport extention {media_type}")

    except OSError as e:
        Trace.error(f"get_modification_timestamp: {e}")
        return None

    json_tmp_path = json_path + "tmp/"
    result_words = import_json(json_tmp_path, filename_two + ".json")
    if result_words is None:
        Trace.error(f"not precessed '{filename}'")
        return None

    words = len(result_words)
    words_per_minute = 60 * words / media_duration

    Trace.result(f"{media_name} - duration: {media_duration:7.2f} sec, {words:4} words => words_per_minute: {words_per_minute: 7.2f}")

    return {
        "duration": media_duration,
        "words": words,
        "words_per_minute": words_per_minute,
    }

def show_parts_results(project: str, results: List[Dict[str, Any]]) -> Tuple[int, int]:
    words_per_minute: List[float] = []

    duration = 0
    words = 0
    for result in results:
        words_per_minute.append(result["words_per_minute"])
        duration += result["duration"]
        words    += result["words"]

    average = np.mean(words_per_minute)
    standard_deviation  = np.std(words_per_minute)

    Trace.result(f"'{project}' duration: {duration/60:6.2f} minutes, {words} words => words_per_minute: average {average:6.2f}, standard_deviation {standard_deviation:5.2f}" )
    return duration, words

def show_complete_results(project: str, duration: float, words: int) -> None:
    Trace.result(f"'{project}' duration: {duration/60:6.2f} minutes, {words} words\n" )

def get_video_length(path: Path | str, filename: str) -> None | float:
    path = Path(path)

    try:
        with (path / filename).open(mode="rb") as media_file:
            media_data = media_file.read()

            media_details: None |Dict[str, Any] = get_video_metadata(io.BytesIO(media_data))
            if media_details is None:
                return None

            media_duration: float = media_details["duration"]

    except OSError as e:
        Trace.error(f"{e}")
        return None

    return media_duration
