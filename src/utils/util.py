"""
    © Jürgen Schoenemeyer, 20.12.2024

    PUBLIC:
     - format_subtitle( start_time: float, end_time: float, text: str, color=True ) -> str
     - format_timestamp(seconds: float, always_include_hours: bool=False, decimal_marker: str=".", fps: float = 30) -> str

     - import_text(folderpath: Path | str, filename: Path|str, show_error: bool=True) -> str | None:
     - import_json_timestamp(folderpath: Path | str, filename: str, show_error: bool=True) -> Tuple[dict | None, float | None]
     - import_json(folderpath: Path | str, filename: str, show_error: bool=True) -> dict | None
     - export_text(folderpath: Path | str, filename: str, text: str, timestamp: int=0, create_new_folder: bool=True, encoding: str = "utf-8", ret_lf: bool=False, show_message: bool=True) -> str | None
     - export_json(folderpath: Path | str, filename: str, data: dict | list, timestamp = None) -> str | None

    class CacheJSON:
      - def __init__(self, path: Path | str, name: str, model: str, reset: bool)
      - def get(self, value_hash: str) -> dict | None
      - def add(self, value_hash: str, value: dict) -> None
      - def flush(self) -> None:

    class ProcessLog (array cache)
      - add
      - get

"""

import codecs
import json

from typing import Tuple
from pathlib import Path

from utils.trace import Trace, Color
from utils.file  import create_folder, get_modification_timestamp, set_modification_timestamp

def format_subtitle( start_time: float, end_time: float, text: str, color=True ) -> str:
    start = format_timestamp(start_time)
    end   = format_timestamp(end_time)

    if color:
        return f"{Color.BOLD.value}{Color.MAGENTA.value}[{start} --> {end}]{Color.NORMAL.value}{text}{Color.RESET.value}"
    else:
        return f"[{start} --> {end}]{text}"

def format_timestamp(seconds: float, always_include_hours: bool=False, decimal_marker: str=".", fps: float = 30) -> str:

    milliseconds = round(seconds * 1000.0)

    if fps:  # match for fps
        fr = round(milliseconds / 1000 * fps)
        milliseconds = int(fr * 1000 / fps)

        # patch for cc editor

        if milliseconds % 100 == 66:  # error with n65 ... n71 (n: 0 ... 9) # 066, 766
            milliseconds -= 2

        if milliseconds > 0:
            if milliseconds % 1000 in (0, 100, 200, 800):  # ok: 100, 300, 400, 600
                milliseconds += 2
            elif milliseconds % 1000 == 900:
                milliseconds += 4

        if milliseconds % 1000 in (33, 933):
            milliseconds -= 2

    hours = milliseconds // 3_600_000
    milliseconds -= hours * 3_600_000

    minutes = milliseconds // 60_000
    milliseconds -= minutes * 60_000

    seconds = milliseconds // 1_000
    milliseconds -= seconds * 1_000

    hours_marker = f"{hours:02d}:" if always_include_hours or hours > 0 else ""
    return (
        f"{hours_marker}{minutes:02d}:{seconds:02d}{decimal_marker}{milliseconds:03d}"
   )

def import_text(folderpath: Path | str, filename: Path|str, show_error: bool=True) -> str | None:
    filepath = Path(folderpath, filename)

    if filepath.is_file():
        try:
            with open(filepath, encoding="utf-8") as file:
                data = file.read()
            return data

        except OSError as error:
            Trace.error(f"{error}")
            return None

    else:
        if show_error:
            Trace.error(f"file not exist {filepath}")
        return None

def import_json_timestamp(folderpath: Path | str, filename: str, show_error: bool=True) -> Tuple[dict | None, float | None]:
    ret = import_json(folderpath, filename, show_error )
    if ret:
        return ret, get_modification_timestamp(Path(folderpath, filename))
    else:
        return None, None

def import_json(folderpath: Path | str, filename: str, show_error: bool=True) -> dict | None:
    result = import_text(folderpath, filename, show_error)
    if result:
        return json.loads(result)
    else:
        return None

def export_text(folderpath: Path | str, filename: str, text: str, timestamp: int=0, create_new_folder: bool=True, encoding: str = "utf-8", ret_lf: bool=False, show_message=True) -> str | None:
    folderpath = Path(folderpath)
    filepath   = Path(folderpath, filename)

    if ret_lf:
        text = text.replace("\n", "\r\n")

    try:
        with codecs.open(str(filepath), "r", encoding) as file:
            text_old = file.read()
    except OSError:
        text_old = ""

    if text == text_old:
        Trace.info(f"not changed '{filepath}'")
        return str(filename)

    if create_new_folder:
        create_folder(folderpath)

    try:
        with codecs.open(str(filepath), "w", encoding) as file:
            file.write(text)

        if timestamp and timestamp != 0:
            set_modification_timestamp(filepath, timestamp)

        if show_message:
            if text_old == "":
                Trace.update(f"created '{filepath}'")
            else:
                Trace.update(f"changed '{filepath}'")

        return str(filename)

    except OSError as error:
        error_msg = str(error).split(":")[0]
        Trace.error(f"{error_msg} - {filepath}")
        return None

def export_json(folderpath: Path | str, filename: str, data: dict | list, timestamp = None) -> str | None:
    text = json.dumps(data, ensure_ascii=False, indent=2)

    return export_text(folderpath, filename, text, encoding = "utf-8", timestamp = timestamp)

class CacheJSON:
    cache: dict = {}
    path: Path = None
    name: str = ""

    def __init__(self, path: Path | str, name: str, model: str, reset: bool):
        self.cache = {}
        self.path = Path(path)
        self.name = name + "-" + model + ".json"

        if Path(self.path, self.name).is_file():
            if not reset:
                self.cache = import_json(self.path, self.name)
                Trace.info(f"{self.path}")
        else:
            create_folder(self.path)

    def get(self, value_hash: str) -> dict | None:
        if value_hash in self.cache:
            return self.cache[value_hash]
        else:
            return None

    def add(self, value_hash: str, value: dict) -> None:
        self.cache[value_hash] = value

    def flush(self) -> None:
        export_json(self.path, self.name, self.cache)

class ProcessLog:
    def __init__(self):
        self.log = []

    def add(self, info):
        self.log.append(info)

    def get(self):
        return self.log
