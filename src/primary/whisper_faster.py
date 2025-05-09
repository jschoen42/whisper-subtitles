"""
    © Jürgen Schoenemeyer, 14.03.2025 00:13

    src/primary/whisper_faster.py

    PUBLIC:
     - precheck_models(models: List) -> bool
     - search_model_path(model_name: str) -> str
     - model_loaded_faster_whisper(model_name: str) -> None | WhisperModel
     - transcribe_fasterwhisper(project_params: Dict, media_params: Dict, cache_nlp: CacheJSON) -> str | Dict
"""
from __future__ import annotations

import hashlib
import io
import logging
import platform
import sys
import time

from pathlib import Path
from typing import Any, Dict, List, Tuple

import arrow

import faster_whisper

from faster_whisper import WhisperModel
from helper.captions import export_srt, export_vtt
from helper.excel_write import export_text_to_speech_excel
from helper.whisper_faster_util import get_settings_transcribe_faster
from helper.whisper_util import are_prompts_allowed, get_filename_parameter, prepare_words, split_to_lines, split_to_sentences
from utils.file import export_json, export_text, get_file_infos, get_modification_timestamp, import_json_timestamp, set_modification_timestamp
from utils.globals import BASE_PATH
from utils.metadata import get_media_info
from utils.prefs import Prefs
from utils.trace import Trace
from utils.util import CacheJSON, format_subtitle

# https://github.com/SYSTRAN/faster-whisper

current_model_name: str = "none"
current_model: Any = None

logging.basicConfig()
logging.getLogger("faster_whisper").setLevel(logging.DEBUG)

def precheck_models(models: List[Tuple[str, str]]) -> bool:
    error = False
    for model in models:
        if search_model_path( model[1] ) is None:
            error = True

    if error:
        return False
    else:
        return True

def search_model_path(model_name: str) -> None | str:
    model_path_all = Prefs.get("whisper.faster_whisper.models.path")
    if model_name not in model_path_all:
        Trace.error(f"'{model_name}' not in defined in 'model_path_all'" )
        return None

    model_base = Prefs.get("whisper.faster_whisper.model_base")
    if not Path(BASE_PATH, model_base).is_dir():
        Trace.fatal(f"model base path '{model_base}' not found")
        return None

    error = False
    model_folder = model_path_all[model_name]

    path = BASE_PATH / model_base / model_folder
    for file in Prefs.get("whisper.faster_whisper.models.files"):
        if not Path(path).is_dir():
            Trace.error(f"'{model_name}' folder '{model_folder}' missing" )
            error = True

        elif not Path(path, file).is_file():
            Trace.error(f"'{model_name}' missing '{file}'" )
            error = True

    if error is False:
        return str(path)
    else:
        return None

def model_loaded_faster_whisper(model_name: str) -> None | WhisperModel:
    global current_model_name

    """
        model_size_or_path: str,
        device: str = "auto",
        device_index: Union[int, List[int]] = 0,
        compute_type: str = "default", # https://opennmt.net/CTranslate2/quantization.html
        cpu_threads: int = 4,
        num_workers: int = 1,
        download_root: Optional[str] = None,
        local_files_only: bool = False,
    """

    global_model_loaded = False

    if not global_model_loaded:
        model_path = search_model_path(model_name)
    else:
        model_path = model_name

    if model_path:
        Trace.info(f"load '{model_path}'")
        cpu_threads = Prefs.get("whisper.faster_whisper.cpu_threads")

        start_time = time.time()
        try:
            model = WhisperModel(model_size_or_path=model_path, device="cpu", compute_type="int8", cpu_threads=cpu_threads)           # int auf CPU, kein float möglich # cpu 7
            # model = WhisperModel(model_name, device="cuda", compute_type="int8_float16") # int auf GPU
            # model = WhisperModel(model_name, device="cuda", compute_type="float16")      # float auf GPU
            current_model_name = model_name
        except ValueError: #  as error:
            model = None
            Trace.fatal(f"not found: {model_path}")
        finally:
            duration = time.time() - start_time

        Trace.info(f"{current_model_name} loaded: {duration:.2f} sec")

        return model
    else:
        return None

def transcribe_fasterwhisper(project_params: Dict[str, Any], media_params: Dict[str, Any], cache_nlp: CacheJSON) -> None | Dict[str, Any]:
    global current_model

    # inModelID     = project_params["modelNumber"]
    model_name      = project_params["modelName"]
    language        = project_params["language"]
    no_prompt       = project_params["noPrompt"]
    beam_size       = project_params["beam"]
    vad_enabled     = project_params["VAD"]

    dictionary_data      = project_params["dictionary"]
    dictionary_timestamp = project_params["dictionary_timestamp"]

    media_type      = project_params["type"]

    path_media      = project_params["mediaPath"]
    path_json_base  = project_params["pathJson"]
    path_text       = project_params["pathText"]
    path_vtt        = project_params["pathVtt"]
    path_srt        = project_params["pathSrt"]
    path_excel      = project_params["pathExcel"]
    path_settings   = project_params["pathSettings"]
    modelname_nlp   = project_params["modelNameNLP"]

    media_name      = media_params["mediaFile"]
    subfolder       = media_params["subFolder"]
    prompt          = media_params["prompt"]
    is_intro        = media_params["isIntro"]

    verbose = True

    condition_on_previous_text = project_params["innerPrompt"]

    if not are_prompts_allowed( model_name ):
        no_prompt = True
        condition_on_previous_text = False
        Trace.warning( f"prompts deactivated for model '{model_name}'" )

    media_pathname = Path(path_media, media_name + "." + media_type)

    whisper_parameter = get_filename_parameter(project_params)
    filename_two = f"{media_name} - {whisper_parameter}"

    start_time = time.time()
    if not media_pathname.is_file():
        Trace.error(f"media not found '{media_pathname}'")
        return None
    else:
        file_info = get_file_infos( path_media, media_name + "." + media_type,  media_type )
        if file_info is None:
            return None

        with Path.open(media_pathname, "rb") as f:
            file = f.read()
            media_md5 = hashlib.md5(file).hexdigest()
            media_info = get_media_info(io.BytesIO(file))
            if media_info is None:
                return None

    duration = time.time() - start_time

    result: Dict[str, Any] = {
        "version": {
            "python": sys.version,
            "faster-whisper": faster_whisper.__version__,
        },
        "settings": {
            "model": model_name,
            "language": language,
            "vad": vad_enabled,
            "beam_size": beam_size,
            "condition_on_previous_text": condition_on_previous_text,
            "no_speech_threshold": None,
            "max_initial_timestamp": 0,
        },
        "cpu": {
            "system": platform.system(),
            "processor": platform.processor(),
            "threads": Prefs.get("whisper.faster_whisper.cpu_threads"),
            "timeMedia": round(duration, 2),
            "timeLoadModel": 0,
            "timeInitTranscribe": 0,
            "timeTranscribe": 0,
        },
        "media": {
            "md5": file_info["md5"],
            "name": media_name,
            "type": media_type,
            "modDate": file_info["date"],
            "duration": round(media_info["duration"], 3),
            "details": {},
        },
        "created": "",
        "language": "",
        "text": "",
        "segments": [],
    }

    path_json     = Path(path_json_base, whisper_parameter)
    path_json_tmp = Path(path_json, "tmp")

    vad_parameter: None | Dict[str, Any] = None
    if vad_enabled:

        # Attributes:
        #   threshold: Speech threshold. Silero VAD outputs speech probabilities for each audio chunk,
        #     probabilities ABOVE this value are considered as SPEECH. It is better to tune this
        #     parameter for each dataset separately, but "lazy" 0.5 is pretty good for most datasets.
        #   neg_threshold: Silence threshold for determining the end of speech. If a probability is lower
        #     than neg_threshold, it is always considered silence. Values higher than neg_threshold
        #     are only considered speech if the previous sample was classified as speech; otherwise,
        #     they are treated as silence. This parameter helps refine the detection of speech
        #      transitions, ensuring smoother segment boundaries.
        #   min_speech_duration_ms: Final speech chunks shorter min_speech_duration_ms are thrown out.
        #   max_speech_duration_s: Maximum duration of speech chunks in seconds. Chunks longer
        #     than max_speech_duration_s will be split at the timestamp of the last silence that
        #     lasts more than 100ms (if any), to prevent aggressive cutting. Otherwise, they will be
        #     split aggressively just before max_speech_duration_s.
        #   min_silence_duration_ms: In the end of each speech chunk wait for min_silence_duration_ms
        #     before separating it
        #   speech_pad_ms: Final speech chunks are padded by speech_pad_ms each side
        #
        # default:
        #  - threshold               = 0.5
        #  - neg_threshold           = threshold - 0.15
        #  - min_speech_duration_ms  = 0
        #  - max_speech_duration_s   = float("inf")
        #  - min_silence_duration_ms = 2000
        #  - speech_pad_ms           = 400

        vad_parameter = {
            "min_speech_duration_ms": 250,
            "speech_pad_ms":          (600, 100),
        }

    cached, timestamp = import_json_timestamp(path_json, filename_two + ".json", show_error=False)

    if cached:
        md5: str = ""
        if "md5" in cached:  # header v1
            md5 = cached["md5"]

            if md5 == media_md5: # migrate from v1 -> v2 (b)

                file_name = filename_two + ".json"
                file_path = Path( path_json, file_name )

                file_info = get_file_infos( path_json, file_name, "json" )
                if file_info is None:
                    return None

                timestamp = get_modification_timestamp(file_path)

                result["created"]  = file_info["date"]
                result["language"] = str(cached["language"]).split("-")[0]
                result["text"]     = cached["text"]
                result["segments"] = cached["segments"]

                export_json(path_json, file_name, result)
                set_modification_timestamp(file_path, timestamp)

        if "media" in cached and "md5" in cached["media"]:
            md5 = cached["media"]["md5"]

        if md5 == "":
            Trace.fatal(f"unknown cache format {Path(path_json, filename_two + '.json')}")

        if md5 == media_md5:
            result = cached

    else:
        if model_name != current_model_name:
            start_time = time.time()
            ret = model_loaded_faster_whisper(model_name)
            if ret is not None:
                current_model = ret
            else:
                Trace.fatal(f"model '{model_name}' not found")

            duration = time.time() - start_time
            result["cpu"]["timeLoadModel"] = round(duration, 2)
            # Trace.result(f"{model_name} loaded: {duration:.2f} sec")
        else:
            Trace.result(f"{model_name} cached")

        if no_prompt:
            curr_prompt = None
        else:
            curr_prompt = prompt

        start_time = time.time()
        segments, info, vad_sampling_rate, vad_speech_chunks = current_model.transcribe(
            str(media_pathname),
            language = language.split("-")[0],
            initial_prompt = curr_prompt,
            condition_on_previous_text = condition_on_previous_text, # für large-v3 unbedingt nötig default True

            beam_size = beam_size,  # default 5 (1 schneller, minimal ungenauer)
                                    # v3: ab beam 3 + condition_on_previous_text TRUE => Wiederholungen)
            # patience  = 1,        # https://www.arxiv-vanity.com/papers/2204.05424/

            word_timestamps = True,

            temperature = [0.0, 0.1, 0.2, 0.4, 0.6, 0.8, 1],  # new 0.1 => delete prompt
            # temperature = [0.0, 0.2, 0.4, 0.6, 0.8, 1],

            prompt_reset_on_temperature = 0.3,

            # best_of = 5
            # patience: 1 [0.5 .. 2]
            # length_penalty = 1 [???] -> to select which to return among the beams or best-of-N samples

            # https://github.com/SYSTRAN/faster-whisper/issues/478
            # repetition_penalty   = default: 1.0 -> 1.1 / 1.2 / ...   (not in OpenAi impl.)
            # no_repeat_ngram_size = default: 0 -> 1 / 2 / 3 (not in OpenAi impl.)

            # compression_ratio_threshold = 2.4

            no_speech_threshold = None,  # default 0.6 verursacht, dass 30 sec Abschnitte komplett leer sind
            max_initial_timestamp = 0,   # default 1.0

            vad_filter = vad_enabled,
            vad_parameters = vad_parameter,
        )
        duration = time.time() - start_time
        result["cpu"]["timeInitTranscribe"] = round(duration, 2)

        result["language"] = info.language

        settings, result["media"]["details"] = get_settings_transcribe_faster(info, media_type, media_info, vad_sampling_rate, vad_speech_chunks)
        export_json(Path(path_settings, whisper_parameter), filename_two + ".json", settings, timestamp = timestamp)

        text = ""
        start_time = time.time()
        for segment in segments:
            segment_info = segment._asdict()
            text += segment_info["text"]
            result["segments"].append(segment_info)

            result_log_list = segment_info["result_log"]
            if result_log_list:
                Trace.warning(f"result_log_list: {result_log_list}")

            if verbose:
                print( format_subtitle( segment_info["start"], segment_info["end"], segment_info["text"] ) )

            time.sleep(0)

        result["text"] = text
        result["created"] = arrow.utcnow().to("Europe/Berlin").format()

        duration = time.time() - start_time
        result["cpu"]["timeTranscribe"] = round(duration, 2)
        Trace.info(f"{media_name} - {duration:.2f} sec")

        export_json(path_json, filename_two + ".json", result, timestamp = timestamp)

    if result["text"] == "":
        Trace.fatal(f"text empty {result}")

    (words,
        sentences,
        _average_probability,  # not used
        _standard_deviation,   # not used
        last_segment_text,
        repetition_error,
        pause_error,
    ) = prepare_words(result, True, is_intro, model_name, language, cache_nlp, media_name)

    export_json(Path(path_json_tmp, modelname_nlp), filename_two + ".json", words, timestamp = timestamp)

    (
        cc,
        text,
        text_combined,
        corrected_details,
        spelling_result,
    ) = split_to_lines(words, dictionary_data)

    if timestamp:
        if len(corrected_details)>0:
            timestamp = max(timestamp, dictionary_timestamp)

    nlp_name = " [" + modelname_nlp + "]"

    text = str(result["text"]).strip() + "\n" + text_combined + "\n\n" + text
    export_text(Path(path_text, whisper_parameter + nlp_name), filename_two + ".txt", text, timestamp = timestamp)

    curr_subfolder = ""
    if len(subfolder) > 0:
        curr_subfolder = subfolder + "/"

    export_text(Path(path_srt, whisper_parameter + nlp_name, curr_subfolder), media_name + ".srt", export_srt(cc), newline = "\r\n", timestamp = timestamp)
    export_text(Path(path_vtt, whisper_parameter + nlp_name, curr_subfolder), media_name + ".vtt", export_vtt(cc), newline = "\r\n", timestamp = timestamp)

    sentence_data = split_to_sentences(words, dictionary_data)
    export_text_to_speech_excel(sentence_data, Path(path_excel, whisper_parameter + nlp_name, curr_subfolder), media_name + ".xlsx") # SubtitleColumnFormat

    return {
        "text":            text_combined,
        "chars":           len(text_combined.replace(" ", "")),
        "words":           len(text_combined.split(" ")),
        "sentences":       sentences,
        "duration":        media_info["duration"],
        "spelling":        spelling_result,
        "corrected":       corrected_details,
        "lastSegment":     last_segment_text,
        "repetitionError": repetition_error,
        "pauseError":      pause_error,
    }
