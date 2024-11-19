# .venv-3.12\Scripts\activate
# python final_srt_vtt.py

import os

from src.utils.prefs import Prefs
from src.utils.trace import Trace, BASE_PATH

from src.helper.captions import import_caption, writefile_srt #, writefile_vtt

PROJECTS: str = "projects.yaml"  # "projects.yaml", "projects_all.yaml"

data_path = BASE_PATH / "../data"

def main():
    Prefs.init("_prefs")
    Prefs.read(PROJECTS)

    if not Prefs.read( PROJECTS, False ):
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
                captions, words, types = import_caption( video_path, file )

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
    main()
