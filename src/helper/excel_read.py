"""
    © Jürgen Schoenemeyer, 25.02.2025 21:58

    src/helper/excel_read.py (calamine)

    https://github.com/tafia/calamine

    PUBLIC:
     - import_project_excel(pathname: Path | str, filename: str)            -> Project | None
     - import_dictionary_excel(pathname: Path | str, filename: str)         -> Dictionary | None
     - import_hunspell_pre_check_excel(pathname: Path | str, filename: str) -> PreCheck | None
     - import_captions_excel(pathname: Path | str, filename: str)           -> Captions | None
     - import_ssml_rules_excel(pathname: Path | str, filename: str)         -> SSML_Rules | None
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, NamedTuple, Tuple, TypedDict

from python_calamine import CalamineError, CalamineWorkbook, WorksheetNotFound

from utils.decorator import duration
from utils.excel import check_double_quotes, check_excel_file_exists
from utils.file import get_modification_timestamp
from utils.trace import Trace

"""
    Excel: Project Infos -> SpeechToText

    Workbook
     - "Projektdetails"

    Worksheet
     - row 1: Main Prompt
     - column 1: File
     - column 2: Sprecher
     - column 3: Variante  (01_LODAS, 02_LuG, 03_LuG_LODAS)
     - column 4: Intro     (x)
     - column 5: no prompt (x)
     - column 6: Prompt

    Result
    {
      "prompt": "DATEV ...",
      "parts": [
        {
          "speaker": "Gunther Schwanke",
          "files": [
            {
              "file": "OSR_2409_KB_Kap_01_00.mp4",
              "folder": "",
              "isIntro": true,
              "prompt": "Gunther Schwanke »Aktuelles aus dem Arbeitsrecht Juli 2024«"
            },
            ...
          ]
        },
        {
          "speaker": "Markus Burgenmeister",
          "files": [
            {
              "file": "OSR_2409_KB_Kap_02_00.mp4",
              "folder": "",
              "isIntro": true,
              "prompt": "Markus Burgenmeister »Optionales Statusfeststellungsverfahren«"
            },
            ...
          ]
        }
        ...
      ]
    }
"""

class Project(TypedDict):
    prompt: str
    parts: List[Speaker]

class Speaker(TypedDict):
    speaker: str
    files: List[File]

class File(TypedDict):
    file: str
    folder: str
    isIntro: bool
    prompt: str

@duration("import '{filename}'")
def import_project_excel(pathname: Path | str, filename: str) -> Project | None:
    pathname = Path(pathname)
    filepath = pathname / filename

    if not check_excel_file_exists(filepath):
        Trace.error(f"file not found: {filepath}")
        return None

    try:
        workbook = CalamineWorkbook.from_path(filepath)
    except CalamineError as err:
        Trace.error(f"CalamineError: {err}")
        return None

    sheet_name = workbook.sheet_names[0]
    data: List[Any] = workbook.get_sheet_by_name(sheet_name).to_python(skip_empty_area=False)

    filename = ""
    speaker = ""
    main_prompt = ""
    speakers: List[str] = []

    part: Dict[str, Speaker] = {}

    for i, row in enumerate(data):
        if i == 0:
            continue # skip header

        if i == 1:
            if row[4].strip().lower() == "x":
                main_prompt = ""
            else:
                main_prompt = row[5].strip()

        else:
            filename = row[0].strip()
            speaker  = row[1].strip()
            project  = row[2].strip()
            isintro  = row[3].strip().lower() == "x"
            noprompt = row[4].strip().lower() == "x"
            prompt   = row[5].strip()

            if noprompt:
                prompt = ""

            if filename:
                if speaker not in speakers:
                    speakers.append(speaker)
                    part[speaker] = {
                        "speaker": speaker,
                        "files": [],
                    }

                part[speaker]["files"].append({
                    "file": filename,
                    "folder": project,
                    "isIntro": isintro,
                    "prompt": prompt,
                })

    result: Project = {
        "prompt": main_prompt,
        "parts": [],
    }

    for value in part.values():
        result["parts"].append(value)

    return result


"""
    Excel: Dictionary

    Workbook
     - normalize
     - allgmein
     - urls
     - Fallbeispiele
     - Spezielles
     - -sz # starts with "-" -> will be ignored (not imported)

    Worksheet
     - 1: original word(s)
     - 2: correction word(s)
     - 3: comment
     - 4: used v2 # reimport of used static with whisper large-v2
     - 5: used v3 # reimport of used static with whisper large-v3

    Return
      - dict original: correction, sheet_name, row
      - list of sheet names
      - file timestamp
"""

class DictionaryEntry(NamedTuple):
    correction: str
    sheet_name: str
    row: int

DictionaryDict = Dict[str, DictionaryEntry]
SheetNames = List[str]

Dictionary = Tuple[
    DictionaryDict,
    SheetNames,
    float,
]

@duration("import '{filename}'")
def import_dictionary_excel(pathname: Path | str, filename: str) -> Dictionary | None:
    pathname = Path(pathname)
    filepath = pathname / filename

    if not check_excel_file_exists(filepath):
        Trace.error(f"file not found: {filepath}")
        return None

    try:
        workbook = CalamineWorkbook.from_path(filepath)
    except CalamineError as err:
        Trace.error(f"CalamineError: {err}")
        return None

    result: DictionaryDict = {}

    for sheet_name in workbook.sheet_names:
        if sheet_name.startswith("-"):
            continue

        data: List[Any]	 = workbook.get_sheet_by_name(sheet_name).to_python(skip_empty_area=False)

        for i, row in enumerate(data):
            if i == 0:
               continue # skip header

            error, original = check_double_quotes(sheet_name, row[0], i+1, filename)
            if error or original == "":
                continue

            error, correction = check_double_quotes(sheet_name, row[1], i+1, filename)
            if not error and correction == "":
                Trace.error(f"'{sheet_name}': row {i+1} '{original}' correction empty")
                continue

            if original == correction:
                Trace.error(f"'{sheet_name}': row {i+1} '{original}' original == correction")
                continue

            if original in result:
                Trace.error(f"'{sheet_name}': row {i+1} '{original}' double entries => '{result[original].correction}' / '{correction}'")
                continue

            result[original] = DictionaryEntry(correction, sheet_name, i+1)

    modification_timestamp = get_modification_timestamp(filepath)

    Trace.result(f"{filename}: {len(result)} entries")
    return result, workbook.sheet_names, modification_timestamp


"""
    Excel: Hunspell PreCheck

    Workbook
     - Abkürzungen
     - Referenten
     - url
     - Musterfälle
     - sonstiges
     - multiple
     - specialDot (deprecated)

    Worksheet
     - 1: Text
     - 2: Anmerkung

    Return:
     - List: abbreviations_with_dot: z.B., Abs., ggf., ...
     - List: singles: www.mydatev.de, KOST1, Meier-Muster, BA-BEA ...
     - List: multiples: 'en block', 'Société à responsabilité limitée'
"""

PreCheck = Tuple[
    List[str],      # abbreviations_with_dot: z.B., Abs., ggf., ...
    List[str],      # singles: www.mydatev.de, KOST1, Meier-Muster, BA-BEA ...
    List[
        List[str]   # ["Microsoft","Customer","Agreement"]
    ],
]

@duration("import '{filename}'")
def import_hunspell_pre_check_excel(pathname: Path | str, filename: str) -> PreCheck | None:
    pathname = Path(pathname)
    filepath = pathname / filename

    if not check_excel_file_exists(filepath):
        Trace.error(f"file not found: {filepath}")
        return None

    try:
        workbook = CalamineWorkbook.from_path(filepath)
    except CalamineError as err:
        Trace.error(f"CalamineError: {err}")
        return None

    abbreviations_with_dot: List[str] = []
    singles: List[str] = []
    multiples: List[List[str]] = []

    for sheet_name in workbook.sheet_names:
        if sheet_name.startswith("-"):
            continue

        try:
            data: List[Any] = workbook.get_sheet_by_name(sheet_name).to_python(skip_empty_area=False)
        except WorksheetNotFound as err:
            Trace.error(f"WorksheetNotFound: '{err}'")
            return None

        for i, row in enumerate(data):
            if i == 0:
               continue # skip header

            error, original = check_double_quotes(sheet_name, row[0], i+1, filename)
            if not error and original != "":
                if sheet_name == "specialDot":
                    abbreviations_with_dot.append(original)
                else:
                    multiple = original.replace("  ", " ").split(" ")
                    if len(multiple) > 1:
                        multiples.append(multiple)
                    elif original[-1] == ".":
                        abbreviations_with_dot.append(original)
                    else:
                        singles.append(original)

    Trace.result(f"{len(singles)} single, {len(multiples)} multiple, abbreviations_with_dot {len(abbreviations_with_dot)}")

    return abbreviations_with_dot, singles, multiples


"""
    Excel: Captions -> TextToSpeech

    Workbook
     - "Projektdetails"

    Worksheet
     - 1: start timecode -> 00:00.500
     - 2: end timecode   -> 00:05.002
     - 3: new segement   -> x
     - 4: type
           -> 'p' Paragraph
           -> 's' Sentence
           -> 'n' nothing
           -> '>' merge
     - 5: text
     - 6: pause          -> 0

    Return
      - Segement
        [start_timecode, end_timecode, [id, text, type, pause], ...]
"""

class ColumnSubtitleExcel(TypedDict):
    start: float
    end:   float
    mark:  str
    type:  str
    text:  str
    pause: float

Captions = List [
    List[ColumnSubtitleExcel]
]

@duration("import '{filename}'")
def import_captions_excel(pathname: Path | str, filename: str) -> Captions | None:
    pathname = Path(pathname)
    filepath = pathname / filename

    if not check_excel_file_exists(filepath):
        Trace.error(f"file not found: {filepath}")
        return None

    try:
        workbook = CalamineWorkbook.from_path(filepath)
    except CalamineError as err:
        Trace.error(f"CalamineError: {err}")
        return None

    sheet_name = workbook.sheet_names[0]
    data: List[Any] = workbook.get_sheet_by_name(sheet_name).to_python(skip_empty_area=False)

    result: List[List[Any]] = []
    curr_start = ""
    curr_end   = ""

    text = ""
    curr_text: List[Any] = []

    for i, row in enumerate(data):
        if i == 0:
            continue # skip header

        start  = row[0].strip()
        end    = row[1].strip()
        marked = row[2].strip().lower() == "x" # start of one ssml
        type   = row[3].strip().lower()
        text   = row[4].strip()
        pause  = row[5]
        if pause == "":
            pause = 0.0

        if type != "" and type not in "psn>":
            Trace.error(f"{filename} unknown type {type} (use 'p' (paragraph), 's' (sentence), 'n' (nothing) or '>' for merge)")
            type = "p"

        if marked:
            if len(curr_text) > 0:
                result.append([curr_start, curr_end, curr_text])
                curr_text = []
            curr_start = start

        curr_text.append({
            "id":    start,
            "text":  text,
            "type":  type,
            "pause": pause,
        })

        curr_end = end

    if text != "":
        result.append([curr_start, curr_end, curr_text])

    return result


"""
    Excel: SSML Rules

    https://docs.aws.amazon.com/polly/latest/dg/supportedtags.html

    Rules: <pre>[key]<post> -> {value} -> template
     - <sub alias>: [i.V.m.] + {in Verbindung mit}        -> <sub alias="in Verbindung mit">i.V.m.</sub>
     - <phoneme>:   <selbst>[buchen]<des> + {bu:xən}      -> selbst<phoneme alphabet="ipa" ph="bu:xən">buchen</phoneme>des
     - <lang>:      <Liquidität >[as a Service] + {en-US} -> Liquidität<lang xml:lang="en-US">as a Service</lang>
     - <say-as>:    [BWA] + {characters}                  -> <say-as interpret-as="characters">BWA</say-as>

    Note
     - <phoneme> not available for AI voices

    Workbook
     - alias
     - phoneme
     - language
     - say-as

    Worksheet
     - 1: pre
     - 2: key
     - 3: post
     - 4: value
     - 5: <template>

    Worksheet - <template>
     - alias:    <sub alias="[value]">[key]</sub>
     - phoneme:  <phoneme alphabet="ipa" ph="[value]">[key]</phoneme>
     - language: <lang xml:lang="[value]">[key]</lang>
     - say_as:   <say-as interpret-as="[value]">[key]</say-as>

    Return
     - alias:    template: <template> / rules: [pre, key, post, value]
     - phoneme:  template: <template> / rules: [pre, key, post, value]
     - language: template: <template> / rules: [pre, key, post, value]
     - say_as:   template: <template> / rules: [pre, key, post, value]
"""

class Rules(TypedDict):
    template: str
    rules: List[List[str]]

SSML_Rules = Dict[str, Rules]

@duration("import '{filename}'")
def import_ssml_rules_excel(pathname: Path | str, filename: str) -> SSML_Rules | None:
    pathname = Path(pathname)
    filepath = pathname / filename

    if not check_excel_file_exists(filepath):
        Trace.error(f"file not found: {filepath}")
        return None

    try:
        workbook = CalamineWorkbook.from_path(filepath)
    except CalamineError as err:
        Trace.error(f"CalamineError: {err}")
        return None

    result: SSML_Rules = {}
    trace_details = "import"

    for sheet_name in workbook.sheet_names:
        if sheet_name.startswith("-"):
            continue

        data: List[Any] = workbook.get_sheet_by_name(sheet_name).to_python(skip_empty_area=False)

        _error, template = check_double_quotes(sheet_name, data[0][4], 1, filename)
        if template == "":
            continue

        rules: List[List[str]] = []
        for i, row in enumerate(data):
            if i == 0:
               continue # skip header

            _error, key = check_double_quotes(sheet_name, row[1], i+1, filename)
            if key != "":
                _error, pre   = check_double_quotes(sheet_name, row[0], i+1, filename)
                _error, post  = check_double_quotes(sheet_name, row[2], i+1, filename)
                _error, value = check_double_quotes(sheet_name, row[3], i+1, filename)
                if value != "":
                    rules.append([pre, key, post, value])

        result[sheet_name] = {
            "template": template,
            "rules": rules,
        }

        trace_details += f" {sheet_name}: {len(rules)},"

    Trace.result(f"{trace_details[:-1]}")
    return result
