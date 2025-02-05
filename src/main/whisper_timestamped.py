"""
    © Jürgen Schoenemeyer, 08.01.2025

    PUBLIC:
     - load_model_whisper(model_name: str) -> Any
     - transcribe_whisper_timestamped(project_params: Dict, media_params: Dict, cache_nlp: CacheJSON) -> str | Dict
"""

import io
import time
import hashlib
import warnings

from typing import Any, Dict
from pathlib import Path

import whisper_timestamped # type: ignore[import-untyped]

from main.whisper import search_model_path

from utils.trace    import Trace
from utils.file     import import_json, export_json, export_text
from utils.util     import CacheJSON
from utils.metadata import get_media_info

from helper.captions     import export_srt, export_vtt
from helper.excel_write  import export_TextToSpeech_excel
from helper.whisper_util import get_filename_parameter, prepare_words, split_to_lines, split_to_sentences

# warnings.simplefilter("ignore", UserWarning)
warnings.simplefilter("ignore", FutureWarning)

# https://github.com/linto-ai/whisper-timestamped
#
# uses "dtw-python" license GPLv2+ !!!
#

current_model_name: str = "none"
current_model: Any = None

def load_model_whisper(model_name: str) -> Any:
    global current_model_name

    """
        name: str,                                         # whisper.available_models()
        device: Optional[Union[str, torch.device]] = None, # "cuda", "cpu"
        download_root: str = None,                         # os.path.join(os.getenv("XDG_CACHE_HOME", default), "whisper")
        in_memory: bool = False,
    """

    model_path = search_model_path(model_name)
    if model_path:
        Trace.info(f"load '{model_path}\\{model_name}.pt'")

        start_time = time.time()
        model = whisper_timestamped.load_model(model_name, download_root=model_path)
        duration = time.time() - start_time
        current_model_name = model_name

        Trace.info(f"{current_model_name} loaded: {duration:.2f} sec")
        return model
    else:
        return None

def transcribe_whisper_timestamped(project_params: Dict[str, Any], media_params: Dict[str, Any], cache_nlp: CacheJSON) -> None | Dict[str, Any]:
    global current_model

    # inModelID     = project_params["modelNumber"]
    model_name      = project_params["modelName"]
    language        = project_params["language"]
    no_prompt       = project_params["noPrompt"]
    beam_size       = project_params["beam"]
    use_vad         = project_params["VAD"]
    dictionary_data = project_params["dictionary"]
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

    if no_prompt:
        curr_prompt = None
    else:
        curr_prompt = prompt

    if use_vad:
        vad = True  # "auditok"
    else:
        vad = None

    param = {
        "language": language.split("-")[0],                       # default "en"
        "fp16": False,                                            # default True
        "verbose": verbose,                                       # default: False

        "vad": vad,                                               # True -> silero, "silero:v3.1", "auditok"

        "beam_size": beam_size,                                   # default: 5
        "best_of": 5,
        "temperature": (0.0, 0.2, 0.4, 0.6, 0.8, 1.0),

        "logprob_threshold": -1.0,                                # default: -1.0
        "no_speech_threshold": None,                              # default: 0.6
        "compression_ratio_threshold": 2.4,                       # default: 2.4
        "condition_on_previous_text": condition_on_previous_text, # default: True

        "initial_prompt": curr_prompt,
        "detect_disfluencies": True,
    }

    media_pathname = Path(path_media, media_name + "." + media_type)

    whisper_parameter = get_filename_parameter(project_params)
    filename_two = f"{media_name} - {whisper_parameter}"

    if not media_pathname.is_file():
        Trace.error(f"media not found '{media_pathname}'")
        return None
    else:
        with open(media_pathname, "rb") as f:
            file = f.read()
            media_md5 = hashlib.md5(file).hexdigest()
            media_info = get_media_info(io.BytesIO(file))
            if media_info is None:
                return None

    settings: Dict[str, Any] = {}
    settings["language"] = language
    settings["duration"] = media_info["duration"]
    settings["transcription_options"] = param

    settings["source"] = {}
    settings["source"]["type"]          = media_type
    settings["source"]["channels"]      = media_info["channels"]
    settings["source"]["sampling_rate"] = media_info["samplingRate"]

    export_json(Path(path_settings, whisper_parameter), filename_two + ".json", settings)

    path_json     = Path(path_json_base, whisper_parameter)
    path_json_tmp = Path(path_json, "tmp")

    Trace.info(f"'{media_name}'")

    result = import_json(path_json, filename_two + ".json", show_error=False)
    if result is not None:
        if "md5" in result:
            if result["md5"] != media_md5:
                Trace.info(f"md5 different - old: {result["md5"]}, new: {media_md5}" )
        else:
            result["md5"] = media_md5
            export_json(path_json, filename_two + ".json", result)

    if result is None or result["md5"] != media_md5:
        if model_name != current_model_name:
            ret = load_model_whisper(model_name)
            if ret is not None:
                current_model = ret
            else:
                Trace.fatal(f"model '{model_name}' not found")

        result = {}
        result["md5"]      = media_md5
        result["type"]     = media_type
        result["duration"] = round(media_info["duration"], 2)
        result["cpuTime"]  = 0
        result["language"] = ""
        result["text"]     = ""
        result["segments"] = []

        start_time = time.time()
        ret = whisper_timestamped.transcribe(current_model, str(media_pathname), **param) # type: ignore[reportArgumentType]
        duration_cpu = time.time() - start_time

        result["cpuTime"]  = round(duration_cpu, 2)
        result["text"]     = ret["text"]
        result["segments"] = ret["segments"]
        result["language"] = ret["language"]
        Trace.info(f"{media_name} - {duration_cpu:.2f} sec")

        export_json(path_json, filename_two + ".json", result)
    else:
        if "type" not in result:
            Trace.update(f"update existing json {filename_two + '.json'}")

            result_new = {}
            result_new["md5"]        = result["md5"]
            result_new["type"]       = media_type
            result_new["duration"]   = round(result["mediaDuration"], 2)
            result_new["cpuTime"]    = round(result["cpuTime"], 2)
            result_new["language"]   = result["language"]
            result_new["text"]       = result["text"]
            result_new["segments"]   = result["segments"]
            export_json(path_json, filename_two + ".json", result_new)

    (  words,
        sentences,
        _average_probability, # not used
        _standard_deviation,  # not used
        last_segment_text,
        repetition_error,
        pause_error
    ) = prepare_words(result, False, is_intro, model_name, language, cache_nlp, media_name)

    export_json(Path(path_json_tmp, modelname_nlp), filename_two + ".json", words)

    (  cc,
        text,
        text_combined,
        corrected_details,
        spelling_result
   ) = split_to_lines(words, dictionary_data)

    nlp_name = " [" + modelname_nlp + "]"

    text = result["text"].strip() + "\n" + text_combined + "\n\n" + text
    export_text(Path(path_text, whisper_parameter + nlp_name), filename_two + ".txt", text)

    curr_subfolder = ""
    if len(subfolder) > 0:
        curr_subfolder = subfolder + "/"

    export_text(Path(path_srt, whisper_parameter + nlp_name, curr_subfolder), media_name + ".srt", export_srt(cc))
    export_text(Path(path_vtt, whisper_parameter + nlp_name, curr_subfolder), media_name + ".vtt", export_vtt(cc))

    sentence_data = split_to_sentences(words, dictionary_data)
    export_TextToSpeech_excel(sentence_data, Path(path_excel, whisper_parameter + nlp_name, curr_subfolder), media_name + ".xlsx") # type: ignore # SubtitleColumnFormat

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
