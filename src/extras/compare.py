import os

from rapidfuzz import fuzz # Levenshtein
import jaro                # type: ignore [import-untyped] # Jaro-Winkler

from utils.trace import Trace
from utils.util import import_json

def compare_file(folderpath: str, project: str, pattern: str) -> None:
    files = os.listdir(folderpath)

    file_infos: list[tuple[str, str]] = []

    Trace.info(f"{project} match: {pattern}")

    for file in files:
        if pattern[0] in file:
            second = file.replace(pattern[0], pattern[1])
            if second in files:
                file_infos.append((file, second))

    for file_info in file_infos:
        first_file = import_json(folderpath, file_info[0])
        if first_file is None:
            continue

        second_file = import_json(folderpath, file_info[1])
        if second_file is None:
            continue

        first_text  = first_file["text"]
        second_text = second_file["text"]
        ret1 = fuzz.ratio(first_text, second_text)

        ret2 = 100 * jaro.jaro_winkler_metric(first_text, second_text)

        Trace.info(f"{file_info[0].replace(" - " + pattern[0] + ".json", ""):18} - fuzzy match: {ret1:6.2f} / {ret2:6.2f}, chars: {len(first_text):4} / {(len(first_text)-len(second_text)):3}")
