# .venv-3.12\Scripts\activate
# python -rename.py

import os
import sys

from pathlib import Path

from utils.globals import BASE_PATH
from utils.prefs   import Prefs
from utils.trace   import Trace
from utils.file    import get_folders_in_folder, get_files_in_folder

PROJECTS: str = "projects_all.yaml"  # "projects.yaml", "projects_all.yaml"

data_path = BASE_PATH / "../data"

# (0, "tiny")
# (1, "base")
# (2, "small")
# (3, "medium")
# (4, "large-v1")

# (5, "large-v2")
# (6, "large-v3")
# (7, "large-v3-turbo")
# (8, "large-v3-turbo-de")

# (9, "large-v2-distil")
# (10, "large-v3-distil")
# (11, "large-v3-crisper")

# new

# ("01", "tiny")
# ("02", "base")
# ("03", "small")
# ("04", "medium")
# ("05", "large-v1")

# ("06", "large-v2")
# ("06", "large-v2•distil")

# ("07", "large-v3")
# ("07", "large-v3•crisper")
# ("07", "large-v3•distil")
# ("07", "large-v3•turbo-de")
# ("07", "large-v3•turbo")

models = {
    "(0) tiny":              "01 tiny",
    "(1) base":              "02 base",
    "(2) small":             "03 small",
    "(3) medium":            "04 medium",
    "(4) large-v1":          "05 large-v1",

    "(5) large-v2":          "06 large-v2",
    "(9) large-v2-distil":   "06 large-v2•distil",
    "(9) large-distil-v2":   "07 large-v2•distil",
    "(7) distil-large-v2":   "07 large-v2•distil",

    "(6) large-v3":          "07 large-v3",
    "(7) large-v3-turbo":    "07 large-v3•turbo",
    "(8) large-v3-turbo-de": "07 large-v3•turbo-de",
    "(10) large-v3-distil":  "07 large-v3•distil",
    "(11) large-v3-crisper": "07 large-v3•crisper",

    "(10) large-distil-v3":  "07 large-v3•distil",
    "(12) large-turbo-v3":   "07 large-v3•turbo",
    "(7) large-v3-de":       "07 large-v3-de",
    "(8) large-v2-de":       "07 large-v2-de",
}

def convert_foldername(folder):

    # engine

    if "faster#" in folder:
        engine = "faster-whisper"

    elif "normal#" in folder:
        engine = "whisper"

    elif "timestamped#" in folder:
        engine = "whisper-timestamped"

    else:
        Trace.fatal( f"unknown engine '{folder}'" )

    # models

    model = None
    for key, value in models.items():
        if key in folder:
            model = value
            break

    if model is None:
        Trace.fatal( f"unknown model '{folder}'" )

    # parameter

    vad = None
    if "VAD-True" in folder:
        vad = "VAD on"
    elif "VAD-False" in folder:
        vad = "VAD off"

    beam = "beam-x"
    if "beam-" in folder:
        id = folder.split("beam-")[1].split("#")[0]
        beam = f"beam-{id}"

    inner_promt = ""
    if "#False#" in folder:
        inner_promt = "inner-prompt off"
    elif "#True#" in folder:
        inner_promt = "inner-prompt on"

    if vad:
        params = f"{vad}, {inner_promt}, {beam}"
    else:
        params = f"{inner_promt}, {beam}"

    return f"[{engine}] [{model}] ({params})"

def convert_filename(filename):
    suffix = Path(filename).suffix
    stem = Path(filename).stem

    page = stem.split(" - ")[0]
    folder = convert_foldername(stem)

    filename = f"{page} - {folder}{suffix}"

    return filename



def rename_project(project_path):

    main_folders = ["04_settings", "05_json" ]

    for main_folder in main_folders:
        path = data_path / project_path / main_folder

        folders = get_folders_in_folder( path )

        check_folder = []
        for folder in folders:
            if folder[0] == "[":
                continue

            new_foldername = convert_foldername(folder)

            if new_foldername in check_folder:
                Trace.error( check_folder )
                Trace.fatal( f"{project_path}/{main_folder} duplicate folder '{new_foldername}'" )
            else:
                check_folder.append(new_foldername)
                print( ">", new_foldername )

            files = get_files_in_folder( path / folder )

            for file in files:
                filename = convert_filename(file)

                # rename file to filename
                os.rename( path / folder / file, path / folder / filename )

            os.rename( path / folder , path / new_foldername  )


    Trace.result(f"rename '{project_path}'")

def rename_folder( folder ):
    Trace.info( f"{folder}")


def main():
    Prefs.init("settings")
    Prefs.load(PROJECTS)

    for project in Prefs.get("projects"):
        rename_project(project)

if __name__ == "__main__":
    Trace.set( debug_mode=True, show_timestamp=False )
    Trace.action(f"Python version {sys.version}")

    main()
