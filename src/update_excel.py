# .venv/Scripts/activate
# python src/update_excel.py

import sys

from utils.prefs import Prefs
from utils.trace import Trace
from utils.file  import import_json

from helper.excel_update import update_dictionary_excel

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
