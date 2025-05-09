"""
    © Jürgen Schoenemeyer, 25.03.2025 17:09

    src/audio.py

    .venv/Scripts/activate
    python src/audio.py
"""
from __future__ import annotations

import sys
import time

from pathlib import Path

from utils.audio import convert_to_wav  # , filter_to_wav
from utils.globals import BASE_PATH
from utils.prefs import Prefs
from utils.trace import Trace

SOURCE_TYPE  = ".mp4"
SAMPLING     = 16000
CHANNELS     = 1

# SOURCE_TYPE  = ".wav"
# SAMPLING     = 48000
# CHANNELS     = 2

PROJECTS: str = "projects.yaml"  # "projects.yaml", "projects_all.yaml"

data_path = BASE_PATH / "../data"

def main() -> None:
    Prefs.init("settings")
    Prefs.load("base.yaml")
    Prefs.load(PROJECTS)

    media_type = Prefs.get("mediaType")

    for project in Prefs.get("projects"):
        if SOURCE_TYPE == ".mp4":
            source = data_path / project / "02_video"
        else:
            source = data_path / project / "03_audio" / media_type

        dest = data_path / project / "03_audio"

        starttime = time.time()
        for filepath in source.iterdir():
            if Path(filepath).suffix == SOURCE_TYPE:
                if media_type == "wav":
                    convert_to_wav( source, Path(dest, "wav"), filepath.name, SAMPLING, CHANNELS, Prefs.get("ffmpeg")["path"] )

        duration = time.time() - starttime
        Trace.info(f"{project} converted: {duration:.2f} sec" )

if __name__ == "__main__":
    Trace.set( debug_mode=True, timezone=False )
    Trace.action(f"Python version {sys.version}")

    try:
        main()
    except KeyboardInterrupt:
        Trace.exception("KeyboardInterrupt")
        sys.exit()
