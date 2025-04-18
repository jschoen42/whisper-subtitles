"""
    © Jürgen Schoenemeyer, 07.04.2025 20:30

    src/utils/trace.py

    static class Trace:
      - Trace.set(debug_mode=True)
      - Trace.set(reduced_mode=True)
      - Trace.set(color=False)
      - Trace.set(timezone=False)
      - Trace.set(timezone="Europe/Berlin") # "UTC", "America/New_York"
      - Trace.set(show_caller=False)
      - Trace.set(appl_folder="/trace/")

      - Trace.action()
      - Trace.result()
      - Trace.info()     # not in reduced mode
      - Trace.update()   # not in reduced mode
      - Trace.download() # not in reduced mode
      - Trace.warning()
      - Trace.error()
      - Trace.exception()
      - Trace.fatal()
      - Trace.debug()    # only in debug mode
      - Trace.wait()     # only in debug mode

      - Trace.decorator()

      - Trace.file_init(["action", "result", "warning", "error"], csv=False)
      - Trace.file_save("./logs", "testTrace")

      - Trace.redirect(function) # -> e.g. qDebug (PySide6)

    static class Color:
      - Color.<color_name>
      - Color.clear(text: str) -> str:
"""
from __future__ import annotations

import importlib.util
import inspect
import platform
import re
import sys

from datetime import datetime
from enum import StrEnum
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, ClassVar, Dict, List
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

if TYPE_CHECKING:
    from types import FrameType

# https://en.wikipedia.org/wiki/ANSI_escape_code#Colors

class Color(StrEnum):
    RESET            = "\033[0m"
    BOLD             = "\033[1m"
    DISABLE          = "\033[2m"
    ITALIC           = "\033[3m"
    UNDERLINE        = "\033[4m"
    INVERSE          = "\033[7m"
    INVISIBLE        = "\033[8m"
    STRIKETHROUGH    = "\033[9m"
    NORMAL           = "\033[11m"

    BLACK            = "\033[30m"  # light/dark mode: #666666 / #666666
    RED              = "\033[31m"  # light/dark mode: #CD3131 / #F14C4C
    GREEN            = "\033[32m"  # light/dark mode: #14CE14 / #23D18B
    YELLOW           = "\033[33m"  # light/dark mode: #B5BA00 / #F5F543
    BLUE             = "\033[34m"  # light/dark mode: #0451A5 / #3B8EEA
    MAGENTA          = "\033[356m" # light/dark mode: #BC05BC / #D670D6
    CYAN             = "\033[36m"  # light/dark mode: #0598BC / #29B8DB
    LIGHT_GRAY       = "\033[37m"  # light/dark mode: #A5A5A5 / #E5E5E5

    BLACK_BG         = "\033[40m"
    RED_BG           = "\033[41m"
    GREEN_BG         = "\033[42m"
    YELLOW_BG        = "\033[43m"
    BLUE_BG          = "\033[44m"
    MAGENTA_BG       = "\033[45m"
    CYAN_BG          = "\033[46m"
    LIGHT_GRAY_BG    = "\033[47m"

    # DARK_GRAY        = "\033[90m"
    # LIGHT_RED        = "\033[91m"
    # LIGHT_GREEN      = "\033[92m"
    # LIGHT_YELLOW     = "\033[93m"
    # LIGHT_BLUE       = "\033[94m"
    # LIGHT_MAGENTA    = "\033[95m"
    # LIGHT_CYAN       = "\033[96m"
    # WHITE            = "\033[97m"

    # DARK_GRAY_BG     = "\033[100m"
    # LIGHT_RED_BG     = "\033[101m"
    # LIGHT_GREEN_BG   = "\033[102m"
    # LIGHT_YELLOW_BG  = "\033[103m"
    # LIGHT_BLUE_BG    = "\033[104m"
    # LIGHT_MAGENTA_BG = "\033[105m"
    # LIGHT_CYAN_BG    = "\033[106m"
    # WHITE_BG         = "\033[107m"

    @staticmethod
    def clear(text: str) -> str:
        return re.sub(r"\033\[[0-9;]*m", "", text)

pattern: Dict[str, str] = {
    "time":      " --> ",
    "action":    " >>> ",
    "result":    " ==> ",
    "important": " ✶✶✶ ", # + magenta

    "info":      "-----",
    "update":    "+++++",
    "download":  ">>>>>",

    "warning":   "✶✶✶✶✶",
    "error":     "#####", # + red
    "exception": "!!!!!", # + red
    "fatal":     "FATAL", # + red

    "debug":     "DEBUG", # only in debug mode
    "wait":      "WAIT ", # only in debug mode

    "decorator": " ooo ",
    "unknown":   " ??? ",
}

class Trace:
    BASE_PATH: Path = Path(sys.argv[0]).parent

    default_base: Path = BASE_PATH.resolve()
    default_base_folder: str = str(default_base).replace("\\", "/")

    settings: ClassVar[Dict[str, Any]] = {
        "appl_folder":    default_base_folder + "/",

        "color":          True,
        "reduced_mode":   False,
        "debug_mode":     False,

        "show_timestamp": True,
        "timezone":       True,

        "show_caller":    True,
    }

    pattern:  ClassVar[List[str]] = []
    messages: ClassVar[List[str]] = []
    csv: bool = False
    output: Callable[..., None] | None = None

    @classmethod
    def set(cls, **kwargs: Any) -> None: # color, reduced_mode, debug_mode, show_timestamp, timezone, show_caller

        for key, value in kwargs.items():
            if key in cls.settings:
                cls.settings[key] = value

                if key == "timezone" and isinstance(value, str):

                    # timezone valid: "UTC", "Europe/Berlin"), "America/New_York" ...

                    if importlib.util.find_spec("tzdata") is None:
                        cls.settings["timezone"] = True
                        Trace.warning(f"please install 'tzdata' for named timezones e.g. '{value}' -> uv add tzdata")

                    else:
                        try:
                            _ = ZoneInfo(value)
                        except ZoneInfoNotFoundError:
                            cls.settings["timezone"] = True
                            Trace.error(f"tzdata '{value}' unknown timezone")

            else:
                Trace.fatal(f"trace settings: unknown parameter '{key}'")

    # info, update, download (not in reduced mode)

    @classmethod
    def info(cls, message: str = "", *optional: Any) -> None:
        if not cls.settings["reduced_mode"]:
            pre = f"{cls._get_time()}{cls._get_pattern()}{cls._get_caller()}"
            cls._show_message(cls._check_file_output(), pre, message, *optional)

    @classmethod
    def update(cls, message: str = "", *optional: Any) -> None:
        if not cls.settings["reduced_mode"]:
            pre = f"{cls._get_time()}{cls._get_pattern()}{cls._get_caller()}"
            cls._show_message(cls._check_file_output(), pre, message, *optional)

    @classmethod
    def download(cls, message: str = "", *optional: Any) -> None:
        if not cls.settings["reduced_mode"]:
            pre = f"{cls._get_time()}{cls._get_pattern()}{cls._get_caller()}"
            cls._show_message(cls._check_file_output(), pre, message, *optional)

    # action, result

    @classmethod
    def action(cls, message: str = "", *optional: Any) -> None:
        pre = f"{cls._get_time()}{cls._get_pattern()}{cls._get_caller()}"
        cls._show_message(cls._check_file_output(), pre, message, *optional)

    @classmethod
    def result(cls, message: str = "", *optional: Any) -> None:
        pre = f"{cls._get_time()}{cls._get_pattern()}{cls._get_caller()}"
        cls._show_message(cls._check_file_output(), pre, message, *optional)

    # important => text MAGENTA, BOLD

    @classmethod
    def important(cls, message: str = "", *optional: Any) -> None:
        pre = f"{cls._get_time()}{Color.MAGENTA}{cls._get_pattern()}{cls._get_caller()}"
        cls._show_message(cls._check_file_output(), pre, f"{Color.MAGENTA}{Color.BOLD}{message}{Color.RESET}", *optional)

    # warning, error, exception, fatal => RED

    @classmethod
    def warning(cls, message: str = "", *optional: Any) -> None:
        pre = f"{cls._get_time()}{cls._get_pattern()}{cls._get_caller()}"
        cls._show_message(cls._check_file_output(), pre, message, *optional)

    @classmethod
    def error(cls, message: str = "", *optional: Any) -> None:
        pre = f"{cls._get_time()}{Color.RED}{cls._get_pattern()}{cls._get_caller()}"
        cls._show_message(cls._check_file_output(), pre, message, *optional)

    @classmethod
    def exception(cls, message: str = "", *optional: Any) -> None:
        pre = f"{cls._get_time()}{Color.RED}{cls._get_pattern()}{cls._get_caller()}"
        cls._show_message(cls._check_file_output(), pre, message, *optional)

    @classmethod
    def fatal(cls, message: str = "", *optional: Any) -> None:
        pre = f"{cls._get_time()}{Color.RED}{Color.BOLD}{cls._get_pattern()}{cls._get_caller()}"
        cls._show_message(cls._check_file_output(), pre, message, *optional)
        raise SystemExit

    # debug, wait (only in debug mode)

    @classmethod
    def debug(cls, message: str = "", *optional: Any) -> None:
        if cls.settings["debug_mode"] and not cls.settings["reduced_mode"]:
            pre = f"{cls._get_time()}{cls._get_pattern()}{cls._get_caller()}"
            cls._show_message(cls._check_file_output(), pre, message, *optional)

    @classmethod
    def wait(cls, message: str = "", *optional: Any) -> None:
        if cls.settings["debug_mode"]:
            pre = f"{cls._get_time()}{cls._get_pattern()}{cls._get_caller()}"
            cls._show_message(cls._check_file_output(), pre, message, *optional)
            try:
                print(f"{Color.RED}{Color.BOLD} >>> Press Any key to continue or ESC to exit <<< {Color.RESET}", end="", flush=True)  # noqa: T201

                if platform.system() == "Windows":
                    import msvcrt

                    key = msvcrt.getch()                      # type: ignore[attr-defined, reportAttributeAccessIssue] # -> Linux
                    print()  # noqa: T201

                else: # unix terminal

                    import termios
                    import tty

                    fd: int = sys.stdin.fileno()
                    old_settings: Any = termios.tcgetattr(fd)  # type: ignore[attr-defined, reportAttributeAccessIssue] # -> Windows
                    try:
                        tty.setraw(sys.stdin.fileno())         # type: ignore[attr-defined, reportAttributeAccessIssue] # -> Windows
                        key = sys.stdin.buffer.read(1)
                    finally:
                        termios.tcsetattr(                     # type: ignore[attr-defined, reportAttributeAccessIssue] # -> Windows
                            fd,
                            termios.TCSADRAIN,                 # type: ignore[attr-defined, reportAttributeAccessIssue] # -> Windows
                            old_settings,
                       )
                        print()  # noqa: T201

                if key == b"\x1b":
                    sys.exit()

            except KeyboardInterrupt:
                sys.exit()

    # decorator -> 12:21:39.836  ooo  <text>: 1.486 sec

    @classmethod
    def decorator(cls, message: str = "", *optional: Any, path: str = "decorator") -> None:
        pre = f"{cls._get_time()}{cls._get_pattern()}{cls._get_decorator_caller(path)}"
        cls._show_message(cls._check_file_output(), pre, message, *optional)

    # file_init, file_save

    @classmethod
    def file_init(cls, pattern_list: None | List[str] = None, csv: bool = False) -> None:
        if pattern_list is None:
            cls.pattern = []
        else:
            cls.pattern = pattern_list
        cls.csv = csv
        cls.messages = []

    @classmethod
    def file_save(cls, path: Path | str, filename: str) -> None:
        trace_path = Path(path)

        text = ""
        for message in Trace.messages:
            text += message + "\n"

        curr_time = cls._get_time_timezone(cls.settings["timezone"]).replace(":", "-")

        try:
            if not trace_path.is_dir():
                Path(path).mkdir(parents=True)

            file_path = trace_path / f"{filename} • {curr_time}.txt"
            with file_path.open(mode="w", encoding="utf-8", newline="\n") as file:
                file.write(text)

        except OSError as e:
            Trace.error(f"write {e}")

        cls.messages = []

    # redirect()

    @classmethod
    def redirect(cls, output: Callable[..., None]) -> None:
        cls.output = output

    # INTERNAL

    @classmethod
    def _check_file_output(cls) -> bool:
        current_frame: FrameType | None = inspect.currentframe()
        if current_frame is None:
            return False

        caller_frame: FrameType | None = current_frame.f_back
        if caller_frame is None:
            return False

        trace_type = caller_frame.f_code.co_name
        return trace_type in cls.pattern

    # show_timestamp=False -> ""
    # timezone=False       -> "13:26:14.768"
    # timezone=True        -> "13:26:14.768+0100"
    # timezone="UTC"       -> "12:26:14.768+0000" (if tzdata is installed)

    @classmethod
    def _get_time(cls) -> str:
        if cls.settings["show_timestamp"]:
            curr_time = cls._get_time_timezone(cls.settings["timezone"])
            return f"{Color.BLUE}{curr_time}{Color.RESET}\t"

        return ""

    @classmethod
    def _get_time_timezone(cls, tz: bool | str) -> str:
        if tz is False:
            return datetime.now().astimezone().strftime("%H:%M:%S.%f")[:-3]

        elif tz is True:
            d = datetime.now().astimezone()
            return d.strftime("%H:%M:%S.%f")[:-3] + d.strftime("%z")

        # "UTC", "Europe/Berlin", "America/New_York", ...

        else:
            timezone = ZoneInfo(tz)
            d = datetime.now().astimezone(timezone)
            return d.strftime("%H:%M:%S.%f")[:-3] + d.strftime("%z")

    # " --> ", " >>> ", " ==> ", "-----", ..., " ooo "

    @staticmethod
    def _get_pattern() -> str:
        current_frame: FrameType | None = inspect.currentframe()
        if current_frame is None:
            return pattern["unknown"] # should never happens

        caller_frame: FrameType | None = current_frame.f_back
        if caller_frame is None:
            return pattern["unknown"] # should never happens

        trace_type = caller_frame.f_code.co_name # info, update, download ...
        if trace_type in pattern:
            return pattern[trace_type]

        return pattern["unknown"]      # should never happens

    # [utils/file.py:413 » export_file]

    @classmethod
    def _get_caller(cls) -> str:
        if cls.settings["show_caller"] is False:
            return f"{Color.RESET} "

        path = inspect.stack()[2][1].replace("\\", "/")
        path = path.split(cls.settings["appl_folder"])[-1]

        current_frame: FrameType | None = inspect.currentframe()
        if current_frame is None:
            return ""

        caller_frame: FrameType | None = current_frame.f_back
        if caller_frame is None:
            return ""

        trace_frame: FrameType | None = caller_frame.f_back
        if trace_frame is None:
            return ""

        line_no = str(trace_frame.f_lineno).zfill(3)

        caller = trace_frame.f_code.co_qualname
        caller = caller.replace(".<locals>.", " → ")

        if caller == "<module>":
            return f"\t{Color.BLUE}[{path}:{line_no}]{Color.RESET}\t"
        else:
            return f"\t{Color.BLUE}[{path}:{line_no} » {caller}]{Color.RESET}\t"

    @classmethod
    def _get_decorator_caller(cls, text: str) -> str:
        if cls.settings["show_caller"] is False:
            return f"{Color.RESET} "

        return f"\t{Color.BLUE}[{text}]{Color.RESET}\t"

    # 13:17:22.499  ==>  [helper/excel_write.py:487 » export_to_excel]  57 media file(s)

    @classmethod
    def _show_message(cls, file_output: bool, pre: str, message: str, *optional: Any) -> None:
        extra = ""
        for opt in optional:
            extra += " > " + str(opt)

        text = f"{pre}{message}{extra}"
        text_no_tabs = text.replace("\t", " ")

        if cls.output is not None:
            cls.output(text_no_tabs)
            return

        if file_output:
            if cls.csv:
                cls.messages.append(Color.clear(text))
            else:
                cls.messages.append(Color.clear(text_no_tabs))

        # https://docs.python.org/3/library/io.html#io.IOBase.isatty

        def is_redirected(stream: Any) -> bool:
            return not hasattr(stream, "isatty") or not stream.isatty()

        if not cls.settings["color"] or is_redirected(stream=sys.stdout):
            text_no_tabs = Color.clear(text_no_tabs)

        # https://docs.python.org/3/library/sys.html#sys.displayhook

        data = (text_no_tabs + "\n").encode("utf-8", "backslashreplace")
        if hasattr(sys.stdout, "buffer"):
            sys.stdout.buffer.write(data)
            sys.stdout.flush()
        else:
            text = data.decode("utf-8", "strict")
            sys.stdout.write(text)
