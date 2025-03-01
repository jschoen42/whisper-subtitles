"""
    © Jürgen Schoenemeyer, 01.03.2025 17:52

    src/final_srt_vtt.py

    .venv/Scripts/activate
    python src/final_srt_vtt.py
"""
from __future__ import annotations

import os

from helper.captions import import_caption, writefile_srt  #, writefile_vtt
from utils.globals import BASE_PATH
from utils.prefs import Prefs
from utils.trace import Trace

PROJECTS: str = "projects.yaml"  # "projects.yaml", "projects_all.yaml"

data_path = BASE_PATH / "../data"

def main() -> None:
    Prefs.init("settings")
    Prefs.load(PROJECTS)

    if not Prefs.load( PROJECTS ):
        Trace.fatal("pref error empty")

    for project in Prefs.get("projects"):
        video_path = data_path / project / "02_video"
        srt_path   = data_path / project / "31_srt_final"
        #vtt_path   = data_path / project / "32_vtt_final"

        sum_types = [0, 0]
        sum_words = 0

        ut = 0
        for file in os.listdir(video_path):
            if file.split(".")[-1] == "srt":
                captions_info = import_caption( video_path, file )
                if captions_info is None:
                    continue

                captions, words, types = captions_info

                sum_words += words
                sum_types[0] += types[0]
                sum_types[1] += types[1]

                if captions:
                    ut += len(captions)
                    writefile_srt( captions, srt_path, file )
                    # writefile_vtt( captions, vtt_path, file.replace(".srt", ".vtt") )
                    # Trace.info("")

        Trace.info(f"{project}, (words: {sum_words}, subtitles all: {ut}, 1-line: {sum_types[0]}, 2-lines: {sum_types[1]})")
        Trace.info("")

if __name__ == "__main__":
    Trace.set( debug_mode=True, timezone=False )
    main()
