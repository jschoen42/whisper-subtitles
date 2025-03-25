"""
    © Jürgen Schoenemeyer, 25.03.2025 17:09

    src/reset.py

    .venv/Scripts/activate
    python src/reset.py
"""
from __future__ import annotations

import sys

from pathlib import Path
from typing import List

from utils.file import delete_folder_tree, get_folders_in_folder
from utils.prefs import Prefs
from utils.trace import Trace

PROJECTS: str = "projects_all.yaml"  # "projects.yaml", "projects_all.yaml"

def reset_project_data(project_path: str) -> None:

    # folders = ["99_trace" ]
    folders: list[str] = ["06_text", "08_vtt", "09_srt", "10_excelExport", "99_trace" ]

    for folder in folders:
        delete_folder_tree(Path("../data", project_path, folder))

    Trace.result(f"reset '{project_path}'")

def clear_cache_spacy(project_path: str) -> None:
    path_base = Path("../data", project_path, "05_json")

    folders: List[str] = get_folders_in_folder(path_base)
    for folder in folders:
        delete_folder_tree( Path(path_base, folder, "nlp") )
        delete_folder_tree( Path(path_base, folder, "tmp") )

def main() -> None:
    Prefs.init("settings")
    Prefs.load(PROJECTS)

    for project in Prefs.get("projects"):
        clear_cache_spacy(project)
        reset_project_data(project)

if __name__ == "__main__":
    Trace.set( debug_mode=True, timezone=False )
    Trace.action(f"Python version {sys.version}")

    main()
