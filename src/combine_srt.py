"""
    © Jürgen Schoenemeyer, 01.03.2025 17:52

    src/combine_srt.py

    .venv/Scripts/activate
    python src/combine_srt.py
"""
from __future__ import annotations

import sys

from typing import Any, Dict, List

from helper.analyse import get_video_length
from helper.captions import Segment, import_caption, writefile_srt
from helper.excel_read import import_project_excel
from utils.globals import BASE_PATH
from utils.prefs import Prefs
from utils.trace import Trace

data_path = BASE_PATH / "../data"

def main() -> None:
    Prefs.init("settings")
    Prefs.load("projects_combine.yaml")

    for project_info in Prefs.get("projects"):
        project  = project_info[0]

        dirname  = data_path / project / "02_video"
        basename = project_info[1]

        parts = project.split("/")
        if len(parts) == 1:
            mainfolder = ""
            folder     = parts[0]
        else:
            mainfolder = parts[0]
            folder     = parts[1]

        videos: List[str] = []
        ret = import_project_excel( data_path / mainfolder / folder, folder + ".xlsx" )
        if ret is None:
            return

        for part in ret["parts"]:
            for entry in part["files"]:
                videos.append( entry["file"] )

        # Step 1: video duration

        duration_one = get_video_length( dirname, basename )

        video_infos: Dict[str, float] = {}
        duration_sum: float = 0.0
        for video in videos:
            duration = get_video_length( dirname, video )
            if duration:
                duration_sum += duration
                video_infos[video] = duration

        Trace.info(f"single file duration: {duration_one:.3f} / sum of single file: {duration_sum:.3f}")

        # Step 2: read all srt files -> dict

        captions_info = {}
        for filename, duration in video_infos.items():
            result = import_caption( dirname, filename.replace(".mp4", ".srt" ) )
            if result is None:
                return

            result_cc: Dict[str, Any] = {
                "duration": duration,
                "cc": result[0],
            }

            captions_info[filename] = result_cc

        # Step 3 combine values and create new file

        offset = 0.0
        section_number = 0
        captions_new: List[Segment] = []

        for part in captions_info:
            duration      = float(captions_info[part]["duration"])
            caption_infos = captions_info[part]["cc"]

            for caption_info in caption_infos:
                section_number += 1

                caption_modified: Segment = {
                    "section": section_number,
                    "start":   offset + caption_info["start"],
                    "end":     offset + caption_info["end"],
                    "text":    caption_info["text"],
                }
                captions_new.append( caption_modified )

            offset += duration

        writefile_srt( captions_new, dirname, basename.replace(".mp4", ".srt") )


if __name__ == "__main__":
    Trace.set( debug_mode=True, show_timestamp=False )
    Trace.action(f"Python version {sys.version}")

    main()
