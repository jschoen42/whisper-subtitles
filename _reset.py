# .venv-3.12\Scripts\activate
# python reset.py

import sys

from pathlib import Path

from src.utils.prefs import Prefs
from src.utils.trace import Trace
from src.utils.file  import delete_folder_tree, get_folders_in_folder

PROJECTS: str = "projects_all.yaml"  # "projects.yaml", "projects_all.yaml"

def reset_project_data(project_path):

    # folders = ["99_trace" ]
    folders = ["06_text", "08_vtt", "09_srt", "10_excelExport", "99_trace" ]

    for folder in folders:
        delete_folder_tree(Path("../data", project_path, folder))

    Trace.result(f"reset '{project_path}'")

def clear_cache_spacy(project_path):
    path_base = Path("../data", project_path, "05_json")

    folders = get_folders_in_folder(path_base)
    for folder in folders:
        delete_folder_tree( Path(path_base, folder, "nlp") )
        delete_folder_tree( Path(path_base, folder, "tmp") )

def main():
    Prefs.init("./_prefs")
    Prefs.read(PROJECTS)

    for project in Prefs.get("projects"):
        clear_cache_spacy(project)
        reset_project_data(project)

if __name__ == "__main__":
    Trace.set( debug_mode=True, show_timestamp=False )
    Trace.action(f"Python version {sys.version}")

    main()
