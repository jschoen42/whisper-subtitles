# .venv/Scripts/activate
# python src/main.py

import sys
import json
import time

from typing import Any, Dict
from pathlib import Path

from utils.globals import BASE_PATH
from utils.prefs   import Prefs
from utils.trace   import Trace
from utils.file    import check_file_exists, export_text
from utils.util    import CacheJSON
from utils.log     import log_clear, log_add, log_get_data
from utils.log     import DictionaryLog

from helper.excel_read   import import_project_excel, import_dictionary_excel
from helper.captions     import seconds_to_timecode_vtt
from helper.spelling     import hunspell_dictionary_init, getSpellStatistic
from helper.whisper_util import init_special_text, are_inner_prompts_possible, prompt_main_normalize, prompt_normalize, get_filename_parameter

from primary.spacy import get_modelname_spacy
from primary.whisper_faster import precheck_models, transcribe_fasterwhisper
from primary.whisper import transcribe_whisper
from primary.whisper_timestamped import transcribe_whisper_timestamped

PROJECTS: str = "projects.yaml"  # "projects.yaml", "projects_all.yaml"

data_path = BASE_PATH / "../data"

# ("01", "tiny")
# ("02", "base")
# ("03", "small")
# ("04", "medium")
# ("05", "large-v1")

# ("06", "large-v2")
# ("06", "large-v2-de")
# ("06", "large-v2•distil-en")

# ("07", "large-v3")
# ("07", "large-v3•crisper")
# ("07", "large-v3•turbo")
# ("07", "large-v3•turbo-de") # fast ohne 'ß'
# ("07", "large-v3•distil-en")

models = [ ("06", "large-v2") ]

beams = [5] # [1, 3, 5, 7, 9] -> keinen signifikater Unterschied zw. 3 ... 9

trace_file_default = ["info", "update", "proof", "warning", "error"]
trace_file_reduced = ["warning"]

reset_cache_spacy: bool = False

def main() -> None:
    Prefs.init("settings")
    Prefs.load("base.yaml")
    Prefs.load("whisper.yaml")
    Prefs.load("hallucination.yaml")
    Prefs.load("spacy.yaml")
    Prefs.load("hunspell.yaml")
    Prefs.load("format_sentence.yaml")
    Prefs.load(PROJECTS)

    whisper_type = Prefs.get("whisper.whisper_type")
    if whisper_type == "faster-whisper":
        if not precheck_models( models ):
            Trace.fatal("missing model(s) -> STOP")

    language   = Prefs.get("language")
    media_type = Prefs.get("mediaType")
    dictionary = Prefs.get("dictionary")
    spelling   = Prefs.get("hunspell")

    Trace.action(f"Whisper type '{whisper_type}' ==> '{PROJECTS}' ({language})")

    init_special_text( language )

    no_prompt  = not Prefs.get("whisper.use_initial_prompt")

    # read details from Excel

    if Prefs.get("projects") is None:
        Trace.fatal("no project defined")

    start = time.perf_counter()

    projects: Dict[str, Any] = {}
    for project in Prefs.get("projects"):
        parts = project.split("/")
        folder = parts[-1]
        mainfolder = "/".join(parts[0:-1])

        ret = import_project_excel(data_path / mainfolder / folder, folder + ".xlsx")
        if ret:
            projects[project] = [project, ret]
        else:
            Trace.fatal(f"project destription not found {project}")

    # check all media exist

    error = False
    for project, data in projects.items():
        path_project = data[0]
        data_project = data[1]

        files = []

        for parts in data_project["parts"]:
            files.append(parts["files"])

        if media_type in ("mp3", "wav", "m4a", "flac"):
            path_media = data_path / path_project / "03_audio" /  media_type
        elif media_type == "mp4":
            path_media = data_path / path_project / "02_video"
        else:
            path_media = ""
            Trace.fatal( f"unknown type '{media_type}'")

        Trace.info(f"check media file exist '{path_project}'")
        for parts in files:
            for media_file in parts:
                filename = media_file["file"].replace(".mp4", "." + media_type)
                if not check_file_exists(path_media, filename):
                    error = True
        if error:
            Trace.fatal( "audios incomplete" )

    # read dictionary for post processing

    data_dictionary, names_dictionary_sheet, dictionary_timestamp = import_dictionary_excel( BASE_PATH / dictionary["path"], dictionary["file"])

    # read hunspell
    # https://hunspell.github.io/
    # https://spylls.readthedocs.io/en/latest/

    hunspell_path = BASE_PATH / spelling["path"] / language
    hunspell_dictionary_init( hunspell_path, spelling["file"][language], language)

    # prepare global trace

    path_trace_main = BASE_PATH / Prefs.get("trace_all")["path"]
    Trace.info()

    for model in models:
        log_dictionary = DictionaryLog( names_dictionary_sheet )

        settings       = ""
        project_all    = 0
        file_count_all = 0
        duration_all   = 0
        chars_all      = 0
        words_all      = 0
        sentences_all  = 0

        for project, data in projects.items():
            path_project = data[0]
            data_project = data[1]

            project_all += 1

            files    = []
            speakers = []

            prompt_main = prompt_main_normalize(data_project["prompt"]).strip()

            for parts in data_project["parts"]:
                files.append(parts["files"])
                speakers.append(parts["speaker"])

            if media_type in ("mp3", "wav", "m4a", "flac"):
                path_media = data_path / path_project / "03_audio" / media_type
            elif media_type == "mp4":
                path_media = data_path / path_project / "02_video"
            else:
                path_media = ""
                Trace.fatal( f"unknown type '{media_type}'")

            path_settings  = data_path / path_project / "04_settings"
            path_json      = data_path / path_project / "05_json"
            path_text      = data_path / path_project / "06_text"

            path_vtt       = data_path / path_project / "08_vtt"
            path_srt       = data_path / path_project / "09_srt"
            path_excel     = data_path / path_project / "10_excelExport"

            path_trace     = data_path / path_project / "99_trace"

            for beam in beams:
                log_clear()

                Trace.set(show_timestamp=True, show_caller=True)
                Trace.file_init(trace_file_default)
                Trace.info(project)
                Trace.info()

                whisper_params = {
                    "whisper":       whisper_type,
                    "modelNumber":   model[0],
                    "modelName":     model[1],
                    "language":      language,
                    "noPrompt":      no_prompt,
                    "innerPrompt":   are_inner_prompts_possible(model[1]),

                    "beam":          beam,
                    "VAD":           Prefs.get("whisper.faster_whisper.use_vad"),

                    "dictionary":           data_dictionary,
                    "dictionary_timestamp": dictionary_timestamp,

                    "type":          media_type,
                    "mediaPath":     path_media,

                    "pathJson":      path_json,
                    "pathText":      path_text,
                    "pathVtt":       path_vtt,
                    "pathSrt":       path_srt,
                    "pathSettings":  path_settings,
                    "pathExcel":     path_excel,

                    "modelNameNLP":  get_modelname_spacy(language),
                }

                settings = get_filename_parameter(whisper_params)  # e.g: "(5) large-v2-fast#True#beam-5#VAD-True"
                project_name = project.split("/")[-1] + " - " + settings

                nlp = CacheJSON(Path(path_json, settings, "nlp"), project_name, get_modelname_spacy(language), reset_cache_spacy)

                file_count = 0
                duration   = 0
                chars      = 0
                words      = 0
                sentences  = 0
                for parts in files:
                    for file_info in parts:
                        file_count += 1
                        file_prompt = ""

                        media_file = file_info["file"]
                        if len(file_info["prompt"]) > 0:
                            prompt = prompt_normalize(file_info["prompt"]).strip()

                            file_prompt = prompt + " " + prompt_main
                        else:
                            file_prompt = prompt_main

                        if file_prompt != "":
                            if file_prompt[-1] not in ".,;:?!":
                                file_prompt += "."

                        tmp = media_file.split(".")
                        tmp.pop()
                        media_file = ".".join(tmp)

                        sub_folder = file_info["folder"]

                        media_params = {
                            "mediaFile": media_file,
                            "subFolder": sub_folder,
                            "prompt":    file_prompt,
                            "isIntro":   file_info["isIntro"],
                        }

                        if whisper_type == "faster-whisper":
                            result = transcribe_fasterwhisper(whisper_params, media_params, nlp)

                        elif whisper_type == "whisper":
                            result = transcribe_whisper(whisper_params, media_params, nlp)

                        elif whisper_type == "whisper-timestamped":
                            result = transcribe_whisper_timestamped(whisper_params, media_params, nlp)

                        else:
                            result = None
                            Trace.fatal(f"unknown whisper type >{whisper_type}<")

                        if result:
                            duration  += result["duration"]
                            chars     += result["chars"]
                            words     += result["words"]
                            sentences += result["sentences"]

                            log_add(
                                media_file,
                                result["text"],
                                result["corrected"],
                                result["lastSegment"],
                                result["repetitionError"],
                                result["pauseError"],
                                result["spelling"],
                            )
                            log_dictionary.add(
                                result["corrected"],
                                result["spelling"]
                            )
                            time.sleep(0)
                            # Trace.info()
                        print()
                        print()

                nlp.flush()

                text_complete, text_corr_complete = log_get_data()

                export_text(path_text, project_name + "-complete.txt", text_complete)
                export_text(path_text, project_name + "-complete.log", text_corr_complete)

                file_count_all += file_count
                duration_all   += duration
                chars_all      += chars
                words_all      += words
                sentences_all  += sentences

                Trace.info()
                Trace.info(f"'{project}' files: {file_count}, duration: {seconds_to_timecode_vtt(duration)}, chars: {chars}, words: {words}, sentences: {sentences}")

                Trace.file_save(path_trace, project_name)
                Trace.set(show_timestamp=True, show_caller=True)

        # _dictionary/Dictionary-DATEV.xlsx -> "correctedAll - .txt"

        (result_excel, result_words, spelling) = log_dictionary.get()

        Trace.set(show_timestamp=False, show_caller=False)
        Trace.file_init(trace_file_reduced)

        for key, value in sorted(result_words.items()):
            Trace.warning(f"'{key}': {value}")

        Trace.file_save(path_trace_main, "correctedAll - " + settings)
        Trace.set(show_timestamp=True, show_caller=True)

        dictionary_used_sorted = {}
        for worksheet, ws_data in result_excel.items():
            dictionary_used_sorted[worksheet] = dict(sorted(ws_data.items()))  # {"normalize": {62: 67, 80: 23, 182: 70 ...

        json_dump = json.dumps(dictionary_used_sorted, ensure_ascii=False, indent=2)
        export_text(path_trace_main, "dictionary_used_sorted - " + settings + ".json", json_dump)

        # Hunspell => "spellingAll - .txt"

        Trace.set(show_timestamp=False, show_caller=False)
        Trace.file_init(trace_file_reduced)

        for key, value in sorted(spelling.items()):
            Trace.warning(f"'{key}': {value}")

        Trace.file_save(path_trace_main, "spellingAll - " + settings)
        Trace.set(show_timestamp=True, show_caller=True)

        d = time.perf_counter() - start

        getSpellStatistic()

        Trace.result(f"projects: {project_all}, filesAll: {file_count_all}, durationAll: {seconds_to_timecode_vtt(duration_all)}, charsAll: {chars_all}, wordsAll: {words_all}, sentencesAll: {sentences_all} ({d:,.2f} sec)")


if __name__ == "__main__":
    Trace.set( debug_mode=True, timezone=False )
    Trace.action(f"Python version {sys.version}")

    try:
        main()
    except KeyboardInterrupt:
        Trace.exception("KeyboardInterrupt")
        sys.exit(0)
