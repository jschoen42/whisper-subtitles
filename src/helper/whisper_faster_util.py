"""
    © Jürgen Schoenemeyer, 08.01.2025

    PUBLIC:
     - get_settings_transcribe_faster(info: Dict, media_type: str, media_info: Dict, vad_sampling_rate: int, speech_chunks: List) -> Tuple[dict, List]:
"""

from typing import Dict, List, Tuple

from utils.trace import Trace
from utils.util  import format_timestamp

"""
TranscriptionInfo(
    language = "de",
    language_probability = 1,
    duration = 94.8303125,
    duration_after_vad = 77.152,
    all_language_probs = None,

    transcription_options = TranscriptionOptions(
        beam_size = 5,
        best_of = 5,
        patience = 1,
        length_penalty = 1,
        repetition_penalty = 1,
        no_repeat_ngram_size = 0,
        log_prob_threshold = -1.0,
        no_speech_threshold = 0.6,
        compression_ratio_threshold = 2.4,
        condition_on_previous_text = False,
        prompt_reset_on_temperature = 0.5,
        temperatures = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0],
        initial_prompt = "",
        prefix = None,
        suppress_blank = True,
        suppress_tokens = [-1],
        without_timestamps = False,
        max_initial_timestamp = 1.0,
        word_timestamps = True,
        prepend_punctuations = '"\'“¿([{-',
        append_punctuations = '"\'.。,，!！?？:：”)]}、'),

    vad_options = VadOptions(
        threshold = 0.5,
        min_speech_duration_ms = 250,
        max_speech_duration_s = inf,
        min_silence_duration_ms = 2000,
        # window_size_samples = 1024,
        speech_pad_ms = 400,
        # speech_pad_offset_ms = 200, # FMG neu
   )
)
"""

def get_settings_transcribe_faster(info: Dict, media_type: str, media_info: Dict, vad_sampling_rate: int, speech_chunks: List) -> Tuple[dict, List]:
    settings: Dict = {}

    try:
        props = [
            "language",
            "language_probability",
            "duration",
            "duration_after_vad",
            "all_language_probs"
        ]
        settings = {p: getattr(info, p) for p in props}
    except Exception as error:
        settings["duration"] = -1
        Trace.error(f"{error}")

    settings["transcription_options"] = {}
    try:
        props = [
            "beam_size",
            "best_of",
            "patience",
            "length_penalty",
            "repetition_penalty",
            "no_repeat_ngram_size",
            "log_prob_threshold",
            "no_speech_threshold",
            "compression_ratio_threshold",
            "condition_on_previous_text",
            "prompt_reset_on_temperature",
            "temperatures",
            "initial_prompt",
            "prefix",
            "suppress_blank",
            "suppress_tokens",
            "without_timestamps",
            "max_initial_timestamp",
            "word_timestamps",
            "prepend_punctuations",
            "append_punctuations"
        ]
        settings["transcription_options"] = {p: info["transcription_options"][p] for p in props}
    except Exception as error:
        settings["duration"] = -1
        Trace.error(f"{error}")

    settings["vad_options"] = None
    try:
        if "vad_options" in info:
            props = [
                "threshold",
                "min_speech_duration_ms",
                "max_speech_duration_s",
                "min_silence_duration_ms",
                "speech_pad_ms"
            ]
            settings["vad_options"] = {p: info["vad_options"][p] for p in props}
    except Exception as error:
        settings["vad_options"] = None
        Trace.error(f"{error}")

    settings["source"] = {}
    settings["source"]["channels"]      = media_info["channels"]
    settings["source"]["sampling_rate"] = media_info["samplingRate"]

    if speech_chunks:
        parts = []
        for entry in speech_chunks:
            start = format_timestamp(entry["start"]/vad_sampling_rate)
            end   = format_timestamp(entry["end"]/vad_sampling_rate)
            parts.append(f"[{start}] --> [{end}]")

        settings["source"]["vad_result"] = parts
    else:
        settings["source"]["vad_result"] = None

    return settings, settings["source"]
