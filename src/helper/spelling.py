"""
    © Jürgen Schoenemeyer, 08.01.2025

    PUBLIC:
     - hunspell_dictionary_init(path: str, filename: str, language: str = "de-DE") -> None:
     - spellcheck(words: List, debug: bool = False) -> Dict:
"""

import re

from typing import Dict, List
from pathlib import Path

from spylls.hunspell import Dictionary # type: ignore # mypy

from utils.globals   import BASE_PATH
from utils.trace     import Trace
from utils.decorator import duration
from utils.prefs     import Prefs
from utils.util      import export_json

from helper.excel_read import import_hunspell_PreCheck_excel

# ../data/_hunspell/de-DE.dic
# ../data/_hunspell/PreCheck_de-DE.xlsx

global_dictionary_data: Dictionary | None = None
global_special_dot_words: List[str] = []             # 'Abs.', 'bspw.', 'bzw.', 'Bzw.', ...
global_precheck_single_words: List[str] = []         # 'AAG', 'AfA', 'AG' ... 'www.datev.de' ... 'und/oder' ...
global_precheck_multiple_words: List[List[str]] = [] # ['Corporate', 'Design'], ['summa', 'summarum'], ['Stock', 'Appreciation', 'Rights'], ... (ws 'multiple')

global_success: Dict[str, int] = {}
global_failure: Dict[str, int] = {}

@duration("Hunspell Dictionary loaded")
def hunspell_dictionary_init(path: Path | str, filename: str, language: str = "de-DE") -> None:
    global global_dictionary_data
    global global_special_dot_words
    global global_precheck_single_words
    global global_precheck_multiple_words

    path = Path(path)

    if global_dictionary_data is None:
        try:
            global_dictionary_data = Dictionary.from_files(str(path / filename))
            Trace.result(f"'{str(path / filename)}' loaded")
        except OSError as err:
            Trace.fatal(f"{err}")

    if len(global_precheck_single_words) == 0:
        filename = "PreCheck_" + language + ".xlsx"

        if language == "de-DE":
            ret = import_hunspell_PreCheck_excel(path, filename)
            if ret:
                (   global_special_dot_words,
                    global_precheck_single_words,
                    global_precheck_multiple_words
                ) = ret
            else:
                Trace.fatal( f"'{filename}' not found" )
        else:
            Trace.fatal(f"unsupported language '{language}'")

# returns not found words: {'Erwerbstatus': 2}

def spellcheck(words: List[str], debug: bool=False) -> Dict[str, int]:
    if global_dictionary_data is None:
        Trace.error("'global_dictionary_data' not loaded")
        return {}

    def check_multiple_words(word: str, index: int) -> int:
        found = False

        word_info: List[str] = []
        for word_info in global_precheck_multiple_words:
            if word == word_info[0]:
                found = True
                for i in range(1, len(word_info)):
                    if index + i >= len(words):
                        found = False
                        break

                    word = words[index + i].strip("'.:,;!?…")  # .split("-")[0]

                    if word != word_info[i]:
                        found = False
                        break

                if found:
                    break

            if found:
                break

        if found:
            Trace.info(f"found {word_info}")
            return len(word_info)
        else:
            return 0

    pattern_paragraph = re.compile(r"\s?§+\d*[a-z]*.?")  # ' §34a', ' §12', ' §§95", ...
    pattern_number = re.compile(r"[\d%,.–€$|&]*")        # '1.001,58', '2,1%', ... , '–', '€', '|', '&'

    result: Dict[str, int] = {}
    i = 0

    while i < len(words):
        print( f"\r{i}", end="")

        word = words[i]

        if pattern_number.fullmatch(word) or pattern_paragraph.fullmatch(word):
            i += 1
        else:
            word = word.strip("':,;!?…")  # without dot !

            found = check_multiple_words(word, i)
            if found > 0:
                i += found
            else:
                if word in global_special_dot_words:
                    i += 1
                else:
                    word = word.strip(".':,;!?…\"()<>")  # e.g. " 'Beim Speichern sofort festschreiben'."

                    if word not in global_precheck_single_words:
                        i += 1
                        try:
                            checked = global_dictionary_data.lookup(word)
                        except Exception as err:
                            Trace.error( f"{i}: {word} -> {err}" )
                            continue

                        if checked:
                            if word in global_success:
                                global_success[word] += 1
                            else:
                                global_success[word] = 1

                            if debug:
                                Trace.info(f"ok: '{word}'")

                        else:
                            if word in global_failure:
                                global_failure[word] += 1
                            else:
                                global_failure[word] = 1

                            Trace.error(f"failed: '{word}'")
                            if word in result:
                                result[word] += 1
                            else:
                                result[word] = 1


    return result

@duration("Hunspell Dictionary result")
def getSpellStatistic():
    path = Prefs.get("trace_all.path")

    # success

    sorted_data = dict(sorted(global_success.items()))
    export_json( BASE_PATH / path, "spelling-unsorted.json", sorted_data )

    sorted_data = dict(sorted(global_success.items(), key=lambda item: item[0].casefold()))
    export_json( BASE_PATH / path, "spelling-casefold.json", sorted_data )

    sorted_data = dict(sorted(global_success.items(), key=lambda item: (-item[1], item[0].casefold())))
    export_json( BASE_PATH / path, "spelling-num_sorted.json", sorted_data )

    # failure

    sorted_data = dict(sorted(global_failure.items(), key=lambda item: item[0].casefold()))
    export_json( BASE_PATH / path, "spelling-failure_casefold.json", sorted_data )

    sorted_data = dict(sorted(global_failure.items(), key=lambda item: (-item[1], item[0].casefold())))
    export_json( BASE_PATH / path, "spelling-failure_num_sorted.json", sorted_data )
