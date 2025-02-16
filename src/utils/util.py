"""
    © Jürgen Schoenemeyer, 16.02.2025

    src/utils/util.py

    PUBLIC:
     - format_subtitle( start_time: float, end_time: float, text: str, color=True ) -> str
     - format_timestamp(seconds: float, always_include_hours: bool=False, decimal_marker: str=".", fps: float = 30) -> str

    class CacheJSON:
     - CacheJSON.init(path: Path | str, name: str, model: str, reset: bool)
     - CacheJSON.get(self, value_hash: str) -> Dict | None
     - CacheJSON.add(self, value_hash: str, value: Dict) -> None
     - CacheJSON.flush(self) -> None:

    class ProcessLog (array cache)
     - ProcessLog.init()
     - ProcessLog.add(info: str)
     - ProcessLog.get() -> List[str]
"""

from typing import Any, Dict, List
from pathlib import Path

from utils.trace import Trace, Color
from utils.file  import create_folder, import_json, export_json

# PUBLIC
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
class CacheJSON:
    cache: Dict[str, Any] = {}
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
