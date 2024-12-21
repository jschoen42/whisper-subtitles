"""
    © Jürgen Schoenemeyer, 21.12.2024

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

from typing import Any, Callable
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

class Color(StrEnum):
    RESET            = "\033[0m"
    BOLD             = "\033[1m"
    DISABLE          = "\033[2m"
    ITALIC           = "\033[3m"
    UNDERLINE        = "\033[4m"
    INVERSE          = "\033[7m"
    INVISIBLE        = "\033[8m"
    STRIKETHROUGH    = "\033[9m"
    NORMAL           = "\033[22m"

    BLACK            = "\033[30m"
    RED              = "\033[31m"
    GREEN            = "\033[32m"
    YELLOW           = "\033[33m"
    BLUE             = "\033[34m"
    MAGENTA          = "\033[35m"
    CYAN             = "\033[36m"
    LIGHT_GRAY       = "\033[37m"
    DARK_GRAY        = "\033[90m"
    LIGHT_RED        = "\033[91m"
    LIGHT_GREEN      = "\033[92m"
    LIGHT_YELLOW     = "\033[93m"
    LIGHT_BLUE       = "\033[94m"
    LIGHT_MAGENTA    = "\033[95m"
    LIGHT_CYAN       = "\033[96m"
    WHITE            = "\033[97m"

    BLACK_BG         = "\033[40m"
    RED_BG           = "\033[41m"
    GREEN_BG         = "\033[42m"
    YELLOW_BG        = "\033[43m"
    BLUE_BG          = "\033[44m"
    MAGENTA_BG       = "\033[45m"
    CYAN_BG          = "\033[46m"
    LIGHT_GRAY_BG    = "\033[47m"
    DARK_GRAY_BG     = "\033[100m"
    LIGHT_RED_BG     = "\033[101m"
    LIGHT_GREEN_BG   = "\033[102m"
    LIGHT_YELLOW_BG  = "\033[103m"
    LIGHT_BLUE_BG    = "\033[104m"
    LIGHT_MAGENTA_BG = "\033[105m"
    LIGHT_CYAN_BG    = "\033[106m"
    WHITE_BG         = "\033[107m"

    @staticmethod
    def clear(text: str) -> str:
        return re.sub(r"\033\[[0-9;]*m", "", text)


pattern = {
    "action":    " >>> ",
    "result":    " ==> ",
    "time":      " --> ",

    "info":      "-----",
    "update":    "+++++",
    "download":  ">>>>>",

    "warning":   "*****",
    "error":     "#####", # + red
    "exception": "!!!!!", # + red
    "fatal":     "FATAL", # + red

    "debug":     "DEBUG", # only in debug mode
    "wait":      "WAIT ", # only in debug mode

    "clear":     "     ", # only internal
}

class Trace:
    BASE_PATH = Path(sys.argv[0]).parent

    default_base = BASE_PATH.resolve()
    default_base_folder = str(default_base).replace("\\", "/")

    settings = {
        "appl_folder":    default_base_folder + "/",

        "color":          True,
        "reduced_mode":   False,
        "debug_mode":     False,

        "show_timestamp": True,
        "timezone":       True,

        "show_caller":    True,
    }

    pattern:list[str]  = []
    messages:list[str] = []
    csv = False
    output = None

    @classmethod
    def set(cls, **kwargs) -> None:
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
    def file_init(cls, pattern_list: None | list = None, csv: bool = False) -> None:
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
    def custom(cls, message: str = "", *optional: Any, path = "custom") -> None:
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
            tz = datetime.now().astimezone()
            return tz.strftime("%H:%M:%S.%f")[:-3] + tz.strftime("%z")

        else:
            try:
                timezone = ZoneInfo(tz)
                tz = datetime.now().astimezone(timezone)
                return tz.strftime("%H:%M:%S.%f")[:-3] + tz.strftime("%z")

            # "tzdata" not installed

            except ZoneInfoNotFoundError:
                tz = datetime.now().astimezone()
                return tz.strftime("%H:%M:%S.%f")[:-3] + tz.strftime("%z")

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
    def __get_custom_caller(cls, text) -> str:
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

        def is_redirected(stream):
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
