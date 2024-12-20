"""
    © Jürgen Schoenemeyer, 20.12.2024

    PUBLIC:
     - log_clear()
     - log_add(mediafile: str, text: str, corrected_details: list[dict], last_segment_text: str, repetition_error: list[dict], pause_error: list[dict], spelling_failed: list[dict] ):
     - log_get_data() -> Tuple[str, str]
    #
    class DictionaryLog:
     - add(self, data: dict, data_spelling: dict) -> None
     - get(self) -> Tuple[dict, dict, dict]

"""

from typing import Tuple

global_complete_text: str = ""
global_complete_text_corr: str = ""

def log_clear():
    global global_complete_text, global_complete_text_corr

    global_complete_text = ""
    global_complete_text_corr = ""

def log_add(
    mediafile: str,
    text: str,
    corrected_details: list[dict],
    last_segment_text: str,
    repetition_error: list[dict],
    pause_error: list[dict],
    spelling_failed: list[dict]
):

    global global_complete_text, global_complete_text_corr

    global_complete_text += mediafile + ":\n" + text + "\n\n"
    global_complete_text_corr += mediafile + ":\n"

    # 1. replaced (always)

    if len(corrected_details) == 0:
        global_complete_text_corr += "> replaced: -"
    else:
        global_complete_text_corr += "> replaced: "
        for i, (key, value) in enumerate(sorted(corrected_details.items())):
            if i > 0:
                global_complete_text_corr += ", "
            global_complete_text_corr += f"'{key}': {value['count']}"

    global_complete_text_corr += "\n"

    # 2. spelling missing (always)

    if len(spelling_failed) == 0:
        global_complete_text_corr += "# spelling missing: -"
    else:
        global_complete_text_corr += "# spelling missing: "
        for i, (key, value) in enumerate(sorted(spelling_failed.items())):
            if i > 0:
                global_complete_text_corr += ", "
            global_complete_text_corr += f"'{key}': {value}"
    global_complete_text_corr += "\n"

    # 3. repetition

    if len(repetition_error) > 0:
        for entry in repetition_error:
            # if entry["model v3]:
            #    global_complete_text_corr += f">> repetition corrected {entry['type']} ({entry['segment']}): {entry['text']}\n"
            # else:

            global_complete_text_corr += f">> possible repetition {entry['type']} ({entry['segment']}): {entry['text']}\n"

    # 4. last segment hallucination removed

    # toDo: vorletztes Segment

    # OSR_2311_LuG_LODAS
    # OSR_2311_Lohn_Kap_02_00:     *** suspicious text *** segment 9/10  - last: False, no_speech_prob: 0.981, duration: 0.56, compressionRatio: 0.87 ' Vielen Dank.'
    # OSR_2311_Lohn_Kap_02_00:     last segment with 'silence text' removed ' Bis zum nächsten Mal.' (no_speech_prob: 0.9806162118911743, duration: 1.08)
    # OSR_2311_Lohn_Kap_02_02_neu: *** suspicious text *** segment 95/96 - last: False, no_speech_prob: 0.995, duration: 0.64, compressionRatio: 0.91 ' Vielen Dank für's Zuschauen.
    # OSR_2311_Lohn_Kap_02_02_neu: *** suspicious text *** segment 96/96 - last: True,  no_speech_prob: 0.995, duration: 0.14, compressionRatio: 0.91 ' Bis zum nächsten Mal.'

    if last_segment_text != "":
        global_complete_text_corr += f">>> removed last segment text '{last_segment_text}'\n"

    # 5. pause error

    for key, value in pause_error.items():
        if len(value) > 0:
            global_complete_text_corr += f"$ {key}: {value}\n"

    global_complete_text_corr += "\n"

def log_get_data() -> Tuple[str, str]:
    return (global_complete_text, global_complete_text_corr)

########################################################################################
#
#  Global DictionaryLog incl. Hunspell (not found)
#    => _traceAll/correctedAll - ... .txt
#    => _traceAll/spellingAll - ... .txt
#    => _traceAll/dictionaryUsedSorted ... .json (*)
#
#  (*) _dictionary/Dictionary-DATEV.xlsx: used word replace
#
#  init: ["normalize", "allgemein", "urls", "Fallbeispiele", "spezielles"]
#
#  add: { "[abc] -> [aBc]": {"count": 2, "worksheet": "allgemein", "row": 126}, ... }
#       { "HV": 1, "K6": 1, ... }
#
#  get: (
#          { "allgemein": {126: 2, 400: 1, 1165: 3, ... }, }
#          { "[abc] -> [aBc]": 2, "[def] -> [deF]" 1, ... }
#          { "HV": 1, "K6": 4, ... }
#      )
#
#######################################################################################

class DictionaryLog:
    def __init__(self, data: dict):
        self.spelling      = {}
        self.word_replaced = {}
        self.excel_used    = {}

        for value in data:
            self.excel_used[value] = {}

    def add(self, data: dict, data_spelling: dict) -> None:

        for key, value in data.items():

            # word replace

            if key in self.word_replaced:
                self.word_replaced[key] += value["count"]
            else:
                self.word_replaced[key]  = value["count"]

            # excel used

            worksheet = value["worksheet"]
            row       = value["row"]
            count     = value["count"]

            if worksheet in self.excel_used:
                if row in self.excel_used[worksheet]:
                    self.excel_used[worksheet][row] += count
                else:
                    self.excel_used[worksheet][row] = count
            else:
                self.excel_used[worksheet] = {row: count}

        for key, value in data_spelling.items():
            if key in self.spelling:
                self.spelling[key] += value
            else:
                self.spelling[key] = value

    def get(self) -> Tuple[dict, dict, dict]:
        return (self.excel_used, self.word_replaced, self.spelling)
