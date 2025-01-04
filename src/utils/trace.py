"""
    © Jürgen Schoenemeyer, 04.01.2025

    class Trace:
      - Trace.set(debug_mode=True)
      - Trace.set(reduced_mode=True)
      - Trace.set(color=False)
      - Trace.set(timezone=False)
      - Trace.set(timezone="Europe/Berlin") # "UTC", "America/New_York"
      - Trace.set(show_caller=False)
      - Trace.set(appl_folder="/trace/")
      #
      - Trace.file_init(["action", "result", "warning", "error"], csv=False)
      - Trace.file_save("./logs", "testTrace")
      #
      - Trace.redirect(function) # -> e.g. qDebug (PySide6)
      #
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

    class Color:
      - Color.<color_name>
      - Color.clear(text: str) -> str:

"""

import platform
import sys
import os
import re
import inspect
import importlib.util

from typing import Any, Callable, Dict, List
from enum import StrEnum
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
from zoneinfo._common import ZoneInfoNotFoundError

system = platform.system()
if system == "Windows":
    import msvcrt
else:
    import tty
    import termios

# https://en.wikipedia.org/wiki/ANSI_escape_code#Colors

def ansi_code(code: int) -> str:
    return f"\033[{code}m"

class Color(StrEnum):
    RESET            = ansi_code(0)
    BOLD             = ansi_code(1)
    DISABLE          = ansi_code(2)
    ITALIC           = ansi_code(3)
    UNDERLINE        = ansi_code(4)
    INVERSE          = ansi_code(7)
    INVISIBLE        = ansi_code(8)
    STRIKETHROUGH    = ansi_code(9)
    NORMAL           = ansi_code(22)

    BLACK            = ansi_code(30)  # light/dark mode: #666666 / #666666
    RED              = ansi_code(31)  # light/dark mode: #CD3131 / #F14C4C
    GREEN            = ansi_code(32)  # light/dark mode: #14CE14 / #23D18B
    YELLOW           = ansi_code(33)  # light/dark mode: #B5BA00 / #F5F543
    BLUE             = ansi_code(34)  # light/dark mode: #0451A5 / #3B8EEA
    MAGENTA          = ansi_code(35)  # light/dark mode: #BC05BC / #D670D6
    CYAN             = ansi_code(36)  # light/dark mode: #0598BC / #29B8DB
    LIGHT_GRAY       = ansi_code(37)  # light/dark mode: #A5A5A5 / #E5E5E5

    # LIGHT_GRAY       = ansi_code(37)
    # DARK_GRAY        = ansi_code(90)
    # LIGHT_RED        = ansi_code(91)
    # LIGHT_GREEN      = ansi_code(92)
    # LIGHT_YELLOW     = ansi_code(93)
    # LIGHT_BLUE       = ansi_code(94)
    # LIGHT_MAGENTA    = ansi_code(95)
    # LIGHT_CYAN       = ansi_code(96)
    # WHITE            = ansi_code(97)

    BLACK_BG         = ansi_code(40)
    RED_BG           = ansi_code(41)
    GREEN_BG         = ansi_code(42)
    YELLOW_BG        = ansi_code(43)
    BLUE_BG          = ansi_code(44)
    MAGENTA_BG       = ansi_code(45)
    CYAN_BG          = ansi_code(46)
    LIGHT_GRAY_BG    = ansi_code(47)

    # DARK_GRAY_BG     = ansi_code(100)
    # LIGHT_RED_BG     = ansi_code(101)
    # LIGHT_GREEN_BG   = ansi_code(102)
    # LIGHT_YELLOW_BG  = ansi_code(103)
    # LIGHT_BLUE_BG    = ansi_code(104)
    # LIGHT_MAGENTA_BG = ansi_code(105)
    # LIGHT_CYAN_BG    = ansi_code(106)
    # WHITE_BG         = ansi_code(107)

    @staticmethod
    def clear(text: str) -> str:
        return re.sub(r"\033\[[0-9;]*m", "", text)


pattern = {
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

    "clear":     " ••• ", # only internal (for decorator, ...)
}

class Trace:
    BASE_PATH = Path(sys.argv[0]).parent

    default_base = BASE_PATH.resolve()
    default_base_folder = str(default_base).replace("\\", "/")

    settings: Dict = {
        "appl_folder":    default_base_folder + "/",

        "color":          True,
        "reduced_mode":   False,
        "debug_mode":     False,

        "show_timestamp": True,
        "timezone":       True,

        "show_caller":    True,
    }

    pattern:list  = []
    messages:list = []
    csv: bool     = False
    output: Callable | None = None

    @classmethod
    def set(cls, **kwargs: Any) -> None:
        for key, value in kwargs.items():
            if key in cls.settings:
                cls.settings[key] = value

                if key == "timezone" and isinstance(value, str):

                    # tzdata installed ?

                    if importlib.util.find_spec("tzdata") is None:
                        print( f"{pattern["warning"]} install 'tzdata' for named timezones")
                        cls.settings[key] = True
                    else:

                        # timezone valid ?

                        try:
                            _ = ZoneInfo(value)
                        except ZoneInfoNotFoundError:
                            print( f"{pattern['error']} tzdata '{value}' unknown timezone")
                            cls.settings[key] = True

            else:
                print(f"trace settings: unknown parameter {key}")

    @classmethod
    def redirect(cls, output: Callable) -> None:
        cls.output = output

    @classmethod
    def file_init(cls, pattern_list: None | List = None, csv: bool = False) -> None:
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

        curr_time = cls.__get_time_timezone(cls.settings["timezone"]).replace(":", "-")

        try:
            if not trace_path.is_dir():
                os.makedirs(path)

            with open(Path(trace_path, f"{filename} • {curr_time}.txt"), "w", encoding="utf-8") as file:
                file.write(text)

        except OSError as err:
            Trace.error(f"[trace_end] write {err}")

        cls.messages = []

    # action, result, info, update, download

    @classmethod
    def action(cls, message: str = "", *optional: Any) -> None:
        pre = f"{cls.__get_time()}{cls.__get_pattern()}{cls.__get_caller()}"
        cls.__show_message(cls.__check_file_output(), pre, message, *optional)

    @classmethod
    def result(cls, message: str = "", *optional: Any) -> None:
        pre = f"{cls.__get_time()}{cls.__get_pattern()}{cls.__get_caller()}"
        cls.__show_message(cls.__check_file_output(), pre, message, *optional)

    @classmethod
    def time(cls, message: str = "", *optional: Any) -> None:
        pre = f"{cls.__get_time()}{cls.__get_pattern()}{cls.__get_custom_caller('duration')}"
        cls.__show_message(cls.__check_file_output(), pre, message, *optional)

    @classmethod
    def custom(cls, message: str = "", *optional: Any, path: str = "custom") -> None:
        pre = f"{cls.__get_time()}{cls.__get_pattern()}{cls.__get_custom_caller(path)}"
        cls.__show_message(cls.__check_file_output(), pre, message, *optional)

    @classmethod
    def info(cls, message: str = "", *optional: Any) -> None:
        if not cls.settings["reduced_mode"]:
            pre = f"{cls.__get_time()}{cls.__get_pattern()}{cls.__get_caller()}"
            cls.__show_message(cls.__check_file_output(), pre, message, *optional)

    @classmethod
    def update(cls, message: str = "", *optional: Any) -> None:
        if not cls.settings["reduced_mode"]:
            pre = f"{cls.__get_time()}{cls.__get_pattern()}{cls.__get_caller()}"
            cls.__show_message(cls.__check_file_output(), pre, message, *optional)

    @classmethod
    def download(cls, message: str = "", *optional: Any) -> None:
        if not cls.settings["reduced_mode"]:
            pre = f"{cls.__get_time()}{cls.__get_pattern()}{cls.__get_caller()}"
            cls.__show_message(cls.__check_file_output(), pre, message, *optional)

    # important => text MAGENTA, BOLD

    @classmethod
    def important(cls, message: str = "", *optional: Any) -> None:
        pre = f"{cls.__get_time()}{Color.MAGENTA}{cls.__get_pattern()}{cls.__get_caller()}"
        cls.__show_message(cls.__check_file_output(), pre, f"{Color.MAGENTA.BOLD}{message}{Color.RESET}", *optional)

    # warning, error, exception, fatal => RED

    @classmethod
    def warning(cls, message: str = "", *optional: Any) -> None:
        pre = f"{cls.__get_time()}{cls.__get_pattern()}{cls.__get_caller()}"
        cls.__show_message(cls.__check_file_output(), pre, message, *optional)

    @classmethod
    def error(cls, message: str = "", *optional: Any) -> None:
        pre = f"{cls.__get_time()}{Color.RED}{cls.__get_pattern()}{cls.__get_caller()}"
        cls.__show_message(cls.__check_file_output(), pre, message, *optional)

    @classmethod
    def exception(cls, message: str = "", *optional: Any) -> None:
        pre = f"{cls.__get_time()}{Color.RED}{cls.__get_pattern()}{cls.__get_caller()}"
        cls.__show_message(cls.__check_file_output(), pre, message, *optional)

    @classmethod
    def fatal(cls, message: str = "", *optional: Any) -> None:
        pre = f"{cls.__get_time()}{Color.RED}{Color.BOLD}{cls.__get_pattern()}{cls.__get_caller()}"
        cls.__show_message(cls.__check_file_output(), pre, message, *optional)
        raise SystemExit

    # debug, wait

    @classmethod
    def debug(cls, message: str = "", *optional: Any) -> None:
        if cls.settings["debug_mode"] and not cls.settings["reduced_mode"]:
            pre = f"{cls.__get_time()}{cls.__get_pattern()}{cls.__get_caller()}"
            cls.__show_message(cls.__check_file_output(), pre, message, *optional)

    @classmethod
    def wait(cls, message: str = "", *optional: Any) -> None:
        if cls.settings["debug_mode"]:
            pre = f"{cls.__get_time()}{cls.__get_pattern()}{cls.__get_caller()}"
            cls.__show_message(cls.__check_file_output(), pre, message, *optional)
            try:
                print(f"{Color.RED}{Color.BOLD} >>> Press Any key to continue or ESC to exit <<< {Color.RESET}", end="", flush=True)

                if system == "Windows":
                    key = msvcrt.getch()
                    print()
                else:
                    fd = sys.stdin.fileno()
                    old_settings = termios.tcgetattr(fd)
                    try:
                        tty.setraw(sys.stdin.fileno())
                        key = sys.stdin.read(1)
                    finally:
                        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
                        print()

                if key == b"\x1b":
                    sys.exit()

            except KeyboardInterrupt:
                sys.exit()


    @classmethod
    def __check_file_output(cls) -> bool:
        trace_type = inspect.currentframe().f_back.f_code.co_name
        return trace_type in list(cls.pattern)

    @classmethod
    def __get_time_timezone(cls, tz: bool | str) -> str:
        if tz is False:
            return datetime.now().strftime("%H:%M:%S.%f")[:-3]

        elif tz is True:
            d = datetime.now().astimezone()
            return tz.strftime("%H:%M:%S.%f")[:-3] + d.strftime("%z")

        else:
            try:
                timezone = ZoneInfo(tz)
                d = datetime.now().astimezone(timezone)
                return d.strftime("%H:%M:%S.%f")[:-3] + d.strftime("%z")

            # "tzdata" not installed

            except ZoneInfoNotFoundError:
                d = datetime.now().astimezone()
                return d.strftime("%H:%M:%S.%f")[:-3] + d.strftime("%z")

    @classmethod
    def __get_time(cls) -> str:
        if cls.settings["show_timestamp"]:
            curr_time = cls.__get_time_timezone(cls.settings["timezone"])
            return f"{Color.BLUE}{curr_time}{Color.RESET}\t"

        return ""

    @staticmethod
    def __get_pattern() -> str:
        trace_type = inspect.currentframe().f_back.f_code.co_name
        if trace_type in pattern:
            return pattern[trace_type]
        else:
            return pattern["clear"]

    @classmethod
    def __get_caller(cls) -> str:
        if cls.settings["show_caller"] is False:
            return f"{Color.RESET} "

        path = inspect.stack()[2][1].replace("\\", "/")
        path = path.split(cls.settings["appl_folder"])[-1]

        lineno = str(inspect.currentframe().f_back.f_back.f_lineno).zfill(3)

        caller = inspect.currentframe().f_back.f_back.f_code.co_qualname # .co_qualname (erst ab 3.11)
        caller = caller.replace(".<locals>.", " → ")

        if caller == "<module>":
            return f"\t{Color.BLUE}[{path}:{lineno}]{Color.RESET}\t"
        else:
            return f"\t{Color.BLUE}[{path}:{lineno} » {caller}]{Color.RESET}\t"

    @classmethod
    def __get_custom_caller(cls, text: str) -> str:
        if cls.settings["show_caller"] is False:
            return f"{Color.RESET} "

        return f"\t{Color.BLUE}[{text}]{Color.RESET}\t"

    @classmethod
    def __show_message(cls, file_output: bool, pre: str, message: str, *optional: Any) -> None:
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

        if not cls.settings["color"] or is_redirected(sys.stdout):
            text_no_tabs = Color.clear(text_no_tabs)

        # https://docs.python.org/3/library/sys.html#sys.displayhook

        bytes = (text_no_tabs + "\n").encode("utf-8", "backslashreplace")
        if hasattr(sys.stdout, "buffer"):
            sys.stdout.buffer.write(bytes)
            sys.stdout.flush()
        else:
            text = bytes.decode("utf-8", "strict")
            sys.stdout.write(text)
