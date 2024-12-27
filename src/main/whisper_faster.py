
"""
    © Jürgen Schoenemeyer, 20.12.2024

    PUBLIC:
     - precheck_models(models: list) -> bool
     - search_model_path(model_name: str) -> str
     - model_loaded_faster_whisper(model_name: str) -> None | WhisperModel
     - transcribe_fasterwhisper(project_params: dict, media_params: dict, cache_nlp: CacheJSON) -> str | dict
"""

import io
import time
import hashlib
import logging

from typing import Any
from pathlib import Path

import arrow

from faster_whisper import WhisperModel

from utils.globals  import BASE_PATH
from utils.prefs    import Prefs
from utils.trace    import Trace
from utils.file     import get_file_infos #, set_modification_timestamp
from utils.util     import import_json_timestamp, export_json, export_text, format_subtitle, CacheJSON
from utils.metadata import get_media_info

from helper.captions import export_srt, export_vtt
from helper.excel import export_TextToSpeech_excel

from helper.whisper_util import get_filename_parameter, are_prompts_allowed, prepare_words, split_to_lines, split_to_sentences
from helper.whisper_faster_util import get_settings_transcribe_faster

# https://github.com/SYSTRAN/faster-whisper

current_model_name: str = "none"
current_model: Any = None

logging.basicConfig()
logging.getLogger("faster_whisper").setLevel(logging.DEBUG)

def precheck_models(models: list) -> bool:
    error = False
    for model in models:
        if search_model_path( model[1] ) is None:
            error = True

    if error:
        return False
    else:
        return True

def search_model_path(model_name: str) -> str:
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
        cpu_threads: int = 0,
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
            duration = time.time() - start_time
            current_model_name = model_name
        except ValueError: #  as error:
            Trace.fatal(f"not found: {model_path}")

        Trace.info(f"{current_model_name} loaded: {duration:.2f} sec")

        return model
    else:
        return None

def transcribe_fasterwhisper(project_params: dict, media_params: dict, cache_nlp: CacheJSON) -> str | dict:
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
        return f"{filename_two} - not found"
    else:
        file_info = get_file_infos( path_media, media_name + "." + media_type,  media_type )

        with open(media_pathname, "rb") as file:
            file = file.read()
            media_md5 = hashlib.md5(file).hexdigest()
            media_info = get_media_info(io.BytesIO(file))

    duration = time.time() - start_time

    result = {
        "media": {
            "md5": file_info["md5"],
            "name": media_name,
            "type": media_type,
            "modDate": file_info["date"],
            "duration": round(media_info["duration"], 2),
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
            "threads": Prefs.get("whisper.faster_whisper.cpu_threads"),
            "timeMedia": round(duration, 2),
            "timeLoadModel": 0,
            "timeInitTranscribe": 0,
            "timeTranscribe": 0,
        },
        "created": "",
        "language": "",
        "text": "",
        "segments": []
    }

    path_json     = Path(path_json_base, whisper_parameter)
    path_json_tmp = Path(path_json, "tmp")

    vad_parameter = None
    if vad_enabled:
        # Attributes:
        # threshold (default 0.5): Speech threshold. Silero VAD outputs speech probabilities for each audio chunk,
        #     probabilities ABOVE this value are considered as SPEECH. It is better to tune this
        #     parameter for each dataset separately, but "lazy" 0.5 is pretty good for most datasets.
        # min_speech_duration_ms (default 250): Final speech chunks shorter min_speech_duration_ms are thrown out.
        # max_speech_duration_s (default "inf"): Maximum duration of speech chunks in seconds. Chunks longer
        #     than max_speech_duration_s will be split at the timestamp of the last silence that
        #     lasts more than 100ms (if any), to prevent aggressive cutting. Otherwise, they will be
        #     split aggressively just before max_speech_duration_s.
        # min_silence_duration_ms (default 2000 - faster, 100 original): In the end of each speech chunk wait for min_silence_duration_ms
        #     before separating it
        # window_size_samples (default 1024 - faster, 1536 original): Audio chunks of window_size_samples size are fed to the silero VAD model.
        #     WARNING! Silero VAD models were trained using 512, 1024, 1536 samples for 16000 sample rate.
        #     Values other than these may affect model performance!!
        # speech_pad_ms (default 400 - faster, 30 original): Final speech chunks are padded by speech_pad_ms each side

        vad_parameter = dict(
            threshold               = 0.5,   # default: 0.5
            min_speech_duration_ms  = 250,   # default: 250
            max_speech_duration_s   = float("inf"),
            min_silence_duration_ms = 2000,  # default: 2000 bisher 1000 war zu kurz
            window_size_samples     = 1024,  # default: 1024 / 512 = fein, 1024 = mittel, 1536 = grob
            speech_pad_ms           = 600,   # 600 ist kompatibler mit prompts - default: 400  / 250 ist zuwenig für den Start, wenn mit prompts
            speech_pad_offset_ms    = 200,   # 200 FMG neu: asymetrisch Auschnitt 200 ms zurück, d.h. [600, 600] -> [800, 400]
            speech_pad_first        = False  # deactivated, was: not is_intro,
       )


    cached, timestamp = import_json_timestamp(path_json, filename_two + ".json", show_error=False)

    if cached:
        md5 = None
        if "media" in cached and "md5" in cached["media"]: #v2
            md5 = cached["media"]["md5"]

        if md5 is None:
            Trace.fatal(f"unknown cache format {Path(path_json, filename_two + ".json")}")

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

        settings, duration = get_settings_transcribe_faster(info, media_type, media_info, vad_sampling_rate, vad_speech_chunks)
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
        pause_error
    ) = prepare_words(result, True, is_intro, model_name, language, cache_nlp, media_name)

    export_json(Path(path_json_tmp, modelname_nlp), filename_two + ".json", words, timestamp = timestamp)

    (cc,
        text,
        text_combined,
        corrected_details,
        spelling_result
   ) = split_to_lines(words, dictionary_data)

    if timestamp:
        if len(corrected_details)>0:
            timestamp = max(timestamp, dictionary_timestamp)

    nlp_name = " [" + modelname_nlp + "]"

    text = result["text"].strip() + "\n" + text_combined + "\n\n" + text
    export_text(Path(path_text, whisper_parameter + nlp_name), filename_two + ".txt", text, timestamp = timestamp)

    curr_subfolder = ""
    if len(subfolder) > 0:
        curr_subfolder = subfolder + "/"

    export_text(Path(path_srt, whisper_parameter + nlp_name, curr_subfolder), media_name + ".srt", export_srt(cc), timestamp = timestamp)
    export_text(Path(path_vtt, whisper_parameter + nlp_name, curr_subfolder), media_name + ".vtt", export_vtt(cc), timestamp = timestamp)

    sentence_data = split_to_sentences(words, dictionary_data)
    export_TextToSpeech_excel(sentence_data, Path(path_excel, whisper_parameter + nlp_name, curr_subfolder), media_name + ".xlsx")

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
