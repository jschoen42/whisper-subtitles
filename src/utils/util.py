"""
    © Jürgen Schoenemeyer, 19.01.2025

    src/utils/util.py

    PUBLIC:
     - format_subtitle( start_time: float, end_time: float, text: str, color=True ) -> str
     - format_timestamp(seconds: float, always_include_hours: bool=False, decimal_marker: str=".", fps: float = 30) -> str

     - import_text(folderpath: Path | str, filename: Path|str, encoding: str="utf-8", show_error: bool=True) -> str | None:
     - import_json_timestamp(folderpath: Path | str, filename: str, show_error: bool=True) -> Tuple[Dict | None, float | None]
     - import_json(folderpath: Path | str, filename: str, show_error: bool=True) -> Dict | None

     - export_text(folderpath: Path | str, filename: str, text: str, encoding: str = "utf-8", timestamp: float=0, ret_lf: bool=False, create_new_folder: bool=True, show_message: bool=True) -> str | None
     - export_json(folderpath: Path | str, filename: str, data: Dict | List, timestamp = None) -> str | None

    class CacheJSON:
      - def __init__(self, path: Path | str, name: str, model: str, reset: bool)
      - def get(self, value_hash: str) -> Dict | None
      - def add(self, value_hash: str, value: Dict) -> None
      - def flush(self) -> None:

    class ProcessLog (array cache)
      - add
      - get
"""

import json

from typing import Any, Dict, List, Tuple
from pathlib import Path

from utils.trace import Trace, Color
from utils.file  import create_folder, get_modification_timestamp, set_modification_timestamp

def format_subtitle( start_time: float, end_time: float, text: str, color: bool=True ) -> str:
    start = format_timestamp(start_time)
    end   = format_timestamp(end_time)

    if color:
        return f"{Color.BOLD}{Color.MAGENTA}[{start} --> {end}]{Color.NORMAL}{text}{Color.RESET}"
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

def import_text(folderpath: Path | str, filename: Path | str, encoding: str="utf-8", show_error: bool=True) -> str | None:
    filepath = Path(folderpath, filename)

    if filepath.is_file():
        try:
            with open(filepath, encoding=encoding) as file:
                data = file.read()
            return data

        except OSError as error:
            Trace.error(f"{error}")
            return None

        except UnicodeDecodeError as error:
            Trace.error(f"{filepath}: {error}")
            return None

    else:
        if show_error:
            Trace.error(f"file not exist {filepath}")
        return None

def import_json_timestamp(folderpath: Path | str, filename: str, show_error: bool=True) -> Tuple[Dict[str, float] | None, float | None]:
    ret = import_json(folderpath, filename, show_error=show_error)
    if ret:
        return ret, get_modification_timestamp(Path(folderpath, filename))
    else:
        return None, None

def import_json(folderpath: Path | str, filename: str, show_error: bool=True) -> Dict[Any, Any] | None:
    result = import_text(folderpath, filename, show_error=show_error)
    if result:
        data: Dict[Any, Any] = json.loads(result)
        return data
    else:
        return None

def export_text(folderpath: Path | str, filename: str, text: str, encoding: str="utf-8", timestamp: None | float=0, ret_lf: bool=False, create_new_folder: bool=True, show_message: bool=True) -> str | None:
    folderpath = Path(folderpath)
    filepath   = Path(folderpath, filename)

    if ret_lf:
        text = text.replace("\n", "\r\n")

    exist = False
    try:
        with open(filepath, "r", encoding=encoding) as file:
            text_old = file.read()
            exist = True
    except OSError:
        text_old = ""

    if exist:
        if text == text_old:
            if show_message:
                Trace.info(f"not changed '{filepath}'")
            return str(filename)

    if create_new_folder:
        create_folder(folderpath)

    try:
        with open(filepath, "w", encoding=encoding) as file:
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

def export_json(folderpath: Path | str, filename: str, data: Dict[Any, Any] | List[Any], timestamp: float | None = None) -> str | None:
    text = json.dumps(data, ensure_ascii=False, indent=2)

    return export_text(folderpath, filename, text, encoding = "utf-8", timestamp = timestamp)

class CacheJSON:
    cache: Dict[Any, Any] = {}
    path: Path = Path()
    name: str = ""

    def __init__(self, path: Path | str, name: str, model: str, reset: bool):
        super().__init__()

        self.cache = {}
        self.path = Path(path)
        self.name = name + "-" + model + ".json"

        if Path(self.path, self.name).is_file():
            if not reset:
                json = import_json(self.path, self.name)
                if json:
                    self.cache = json
                    Trace.info(f"{self.path}")
        else:
            create_folder(self.path)

    def get(self, value_hash: str) -> Dict[Any, Any] | None:
        if value_hash in self.cache:
            data: Dict[Any, Any] = self.cache[value_hash]
            return data
        else:
            return None

    def add(self, value_hash: str, value: Dict[Any, Any]) -> None:
        self.cache[value_hash] = value

    def flush(self) -> None:
        export_json(self.path, self.name, self.cache)

class ProcessLog:
    def __init__(self) -> None:
        super().__init__()
        self.log: List[str] = []

    def add(self, info: str) -> None:
        self.log.append(info)

    def get(self) -> List[str]:
        return self.log
