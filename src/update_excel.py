"""
    © Jürgen Schoenemeyer, 01.03.2025 17:52

    src/update_excel.py

    .venv/Scripts/activate
    python src/update_excel.py
"""
from __future__ import annotations

import sys

from helper.excel_update import update_dictionary_excel
from utils.file import import_json
from utils.prefs import Prefs
from utils.trace import Trace

def main() -> None:
    Prefs.init("settings")
    Prefs.load("base.yaml")

    path_dictionary = Prefs.get("dictionary.path")

    used_info = import_json( path_dictionary, "dictionaryUsedSorted-v2.json" )
    if used_info:
        update_dictionary_excel( path_dictionary, "Dictionary-DATEV.xlsx", "Dictionary-Update-v2.xlsx", "used v2", used_info)

    # used_info = import_json( path_dictionary, "dictionaryUsedSorted-v3.json" )
    # if used_info:
    #     update_dictionary_excel( path_dictionary, "Dictionary-DATEV.xlsx", "Dictionary-Update-v3.xlsx", "used v3", used_info)

    used_info = import_json( path_dictionary, "dictionaryUsedSorted-v3.json" )
    if used_info:
       update_dictionary_excel( path_dictionary, "Dictionary-Update-v2.xlsx", "Dictionary-Update-v2v3.xlsx", "used v3", used_info)

    # used_info = import_json( path_dictionary, "dictionaryUsedSorted-sz.json" )
    # if used_info:
    #     update_dictionary_excel( path_dictionary, "Dictionary-DATEV.xlsx", "Dictionary-Update-sz.xlsx", "used v3", used_info)


if __name__ == "__main__":
    Trace.set( debug_mode=True, timezone=False )
    Trace.action(f"Python version {sys.version}")

    main()
