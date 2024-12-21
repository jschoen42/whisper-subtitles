# .venv/Scripts/activate
# python src/combine_srt.py

import sys

from utils.globals import BASE_PATH
from utils.prefs   import Prefs
from utils.trace   import Trace

from helper.excel    import import_project_excel
from helper.analyse  import get_video_length
from helper.captions import import_caption, writefile_srt

data_path = BASE_PATH / "../data"

def main():
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

        videos: list = []
        ret = import_project_excel( data_path / mainfolder / folder, folder + ".xlsx" )

        for part in ret["parts"]:
            for entry in part["files"]:
                videos.append( entry["file"] )

        # Step 1: video duration

        duration_one = get_video_length( dirname, basename )

        video_infos: dict = {}
        duration_sum: int = 0
        for video in videos:
            duration = get_video_length( dirname, video )
            if duration:
                duration_sum += duration
                video_infos[video] = duration

        Trace.info(f"single file duration: {duration_one:.3f} / sum of single file: {duration_sum:.3f}")

        # Step 2: read all srt files -> dict

        captions_info = {}
        for filename, duration in video_infos.items():
            tmp = {}
            tmp["duration"] = duration
            tmp["cc"], _words, _line_types = import_caption( dirname, filename.replace(".mp4", ".srt" ) )

            captions_info[filename] = tmp

        # Step 3 combine values and create new file

        offset = 0
        section_number = 0
        captions_new = []

        for part, _value in captions_info.items():
            duration      = captions_info[part]["duration"]
            caption_infos = captions_info[part]["cc"]

            for caption_info in caption_infos:
                section_number += 1

                caption_modified = {}
                caption_modified["section"] = section_number
                caption_modified["start"]   = offset + caption_info["start"]
                caption_modified["end"]     = offset + caption_info["end"]
                caption_modified["text"]    = caption_info["text"]
                captions_new.append( caption_modified )

            offset += duration

        writefile_srt( captions_new, dirname, basename.replace(".mp4", ".srt") )


if __name__ == "__main__":
    Trace.set( debug_mode=True, show_timestamp=False )
    Trace.action(f"Python version {sys.version}")

    main()
