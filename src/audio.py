# .venv/Scripts/activate
# python src/audio.py

import sys
import os
import time

from pathlib import Path

from utils.globals import BASE_PATH
from utils.prefs   import Prefs
from utils.trace   import Trace

from utils.audio import convert_to_wav # , filter_to_wav

SOURCE_TYPE  = ".mp4"
SAMPLING     = 16000
CHANNELS     = 1

# SOURCE_TYPE  = ".wav"
# SAMPLING     = 48000
# CHANNELS     = 2

PROJECTS: str = "projects.yaml"  # "projects.yaml", "projects_all.yaml"

data_path = BASE_PATH / "../data"

def main():
    Prefs.init("settings")
    Prefs.read("base.yaml")
    Prefs.read(PROJECTS)

    media_type = Prefs.get("mediaType")

    for project in Prefs.get("projects"):
        if SOURCE_TYPE == ".mp4":
            source = data_path / project / "02_video"
        else:
            source = data_path / project / "03_audio" / media_type

        dest = data_path / project / "03_audio"

        starttime = time.time()
        for filename in os.listdir(source):
            if Path(filename).suffix == SOURCE_TYPE:
                if media_type == "wav":
                    convert_to_wav( source, Path(dest, "wav"), filename, SAMPLING, CHANNELS, Prefs.get("ffmpeg")["path"] )

        duration = time.time() - starttime
        Trace.info(f"{project} converted: {duration:.2f} sec" )

if __name__ == "__main__":
    Trace.set( debug_mode=True, timezone=False )
    Trace.action(f"Python version {sys.version}")

    main()
