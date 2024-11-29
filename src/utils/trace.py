"""
    (c) Jürgen Schoenemeyer, 29.11.2024

    PUBLIC:
    remove_colors(text: str) -> str:

    @timeit(pre_text: str = "", rounds: int = 1)

    @timeit("argon2 (20 rounds)", 20) # test with 20 rounds => average duration for a round

    @timeit("ttx => font '{0}'")      # 0 -> args
    @timeit("ttx => font '{type}'")   # type -> kwargs

    class Trace:

        Trace.set(appl_folder="/trace/", debug_mode=False, reduced_mode=False, show_timestamp=True, time_zone="")
        Trace.set(color=False)

        Trace.file_init(["action", "result", "warning", "error"], csv=False) # csv with TAB instead of comma
        Trace.file_save("./logs", "testTrace")

        Trace.action()
        Trace.result()
        Trace.info()     # not in reduced mode
        Trace.update()   # not in reduced mode
        Trace.download() # not in reduced mode

        Trace.warning()
        Trace.error()
        Trace.exception()
        Trace.fatal()

        Trace.debug()    # only in debug mode
        Trace.wait()     # only in debug mode

    class ProcessLog (array cache)
        - add
        - get

"""

import platform
import sys
import os
import re
import inspect
import time

from enum import StrEnum
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
from zoneinfo._common import ZoneInfoNotFoundError

BASE_PATH = Path(sys.argv[0]).parent

system = platform.system()
if system == "Windows":
    import msvcrt
else:
    import tty
    import termios

# force tomezone available, if "tzdata" is installed
# DEFAULT_TIMEZONE = "UTC"
DEFAULT_TIMEZONE = "Europe/Berlin"

# https://en.wikipedia.org/wiki/ANSI_escape_code#Colors

class Color(StrEnum):
    RESET         = "\033[0m"
    BOLD          = "\033[1m"
    DISABLE       = "\033[2m"
    ITALIC        = "\033[3m"
    UNDERLINE     = "\033[4m"
    INVERSE       = "\033[7m"
    INVISIBLE     = "\033[8m"
    STRIKETHROUGH = "\033[9m"
    NORMAL        = "\033[22m"

    BLACK         = "\033[30m"
    RED           = "\033[31m"
    GREEN         = "\033[32m"
    BLUE          = "\033[34m"
    PURPLE        = "\033[35m"
    CYAN          = "\033[36m"
    GREY          = "\033[37m"

    BLACK_BG      = "\033[40m"
    RED_BG        = "\033[41m"
    GREEN_BG      = "\033[42m"
    BLUE_BG       = "\033[44m"
    PURPLE_BG     = "\033[45m"
    CYAN_BG       = "\033[46m"
    GREY_BG       = "\033[47m"

def remove_colors(text: str) -> str:
    return re.sub(r"\033\[[0-9;]*m", "", text)


# decorator for time measure

def timeit(pre_text: str = "", rounds: int = 1):
    def decorator(func):
        def wrapper(*args, **kwargs):
            start_time = time.perf_counter()

            result = func(*args, **kwargs)

            end_time = time.perf_counter()
            total_time = (end_time - start_time) / rounds

            def replace_args(match):
                word = match.group(1)
                if word.isnumeric():
                    return str(args[int(word)]) # {1} -> args[1]
                else:
                    return kwargs.get(word)     # {type} -> kwargs["type"]

            pattern = r"\{(.*?)\}"
            pretext = re.sub(pattern, replace_args, pre_text)

            text = f"{Color.GREEN}{Color.BOLD}{total_time:.3f} sec{Color.RESET}"
            if pretext == "":
                Trace.time(f"{text}")
            else:
                Trace.time(f"{pretext}: {text}")

            return result
        return wrapper
    return decorator

pattern = {
    "clear":     "     ", # only internal

    "action":    " >>> ",
    "result":    " ==> ",
    "time":      " --> ",

    "info":      "-----",
    "update":    "+++++",
    "download":  ">>>>>",

    "warning":   "*****",
    "error":     "#####", # + rot
    "exception": "!!!!!",
    "fatal":     "FATAL",

    "debug":     "DEBUG", # only in special debug mode
    "wait":      "WAIT ", # only in special debug mode
}

class Trace:
    # default_base_folder = os.getcwd().replace("\\", "/").split("/")[-1]

    default_base = BASE_PATH.resolve()
    default_base_folder = str(default_base).replace("\\", "/")

    # sys.stdout.encoding = "utf-8"

    settings = {
        "appl_folder":    default_base_folder + "/",

        "color":          True,
        "reduced_mode":   False,
        "debug_mode":     False,

        "show_timestamp": True,
        "show_caller":    True,
        "time_zone":      DEFAULT_TIMEZONE,
    }

    pattern:list[str]  = []
    messages:list[str] = []
    csv = False

    @classmethod
    def set(cls, **kwargs) -> None:
        for key, value in kwargs.items():
            if key in cls.settings:
                cls.settings[key] = value
            else:
                print(f"trace settings: unknown parameter {key}")

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

        try:
            timezone = ZoneInfo(cls.settings["time_zone"])
            curr_time = datetime.now().astimezone(timezone).strftime("%Y.%d.%m • %H-%M-%S")
        except ZoneInfoNotFoundError:
            curr_time = datetime.now().strftime("%Y.%d.%m • %H-%M-%S") # "tzdata" not installed

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
    def action(cls, message: str = "", *optional: any) -> None:
        pre = f"{cls.__get_time()}{cls.__get_pattern()}{cls.__get_caller()}"
        cls.__show_message(cls.__check_file_output(), pre, message, *optional)

    @classmethod
    def result(cls, message: str = "", *optional: any) -> None:
        pre = f"{cls.__get_time()}{cls.__get_pattern()}{cls.__get_caller()}"
        cls.__show_message(cls.__check_file_output(), pre, message, *optional)

    @classmethod
    def time(cls, message: str = "", *optional: any) -> None:
        pre = f"{cls.__get_time()}{cls.__get_pattern()}{cls.__get_custom_caller('duration')}"
        cls.__show_message(cls.__check_file_output(), pre, message, *optional)

    @classmethod
    def info(cls, message: str = "", *optional: any) -> None:
        if not cls.settings["reduced_mode"]:
            pre = f"{cls.__get_time()}{cls.__get_pattern()}{cls.__get_caller()}"
            cls.__show_message(cls.__check_file_output(), pre, message, *optional)

    @classmethod
    def update(cls, message: str = "", *optional: any) -> None:
        if not cls.settings["reduced_mode"]:
            pre = f"{cls.__get_time()}{cls.__get_pattern()}{cls.__get_caller()}"
            cls.__show_message(cls.__check_file_output(), pre, message, *optional)

    @classmethod
    def download(cls, message: str = "", *optional: any) -> None:
        if not cls.settings["reduced_mode"]:
            pre = f"{cls.__get_time()}{cls.__get_pattern()}{cls.__get_caller()}"
            cls.__show_message(cls.__check_file_output(), pre, message, *optional)

    # warning, error, exception, fatal => RED

    @classmethod
    def warning(cls, message: str = "", *optional: any) -> None:
        pre = f"{cls.__get_time()}{cls.__get_pattern()}{cls.__get_caller()}"
        cls.__show_message(cls.__check_file_output(), pre, message, *optional)

    @classmethod
    def error(cls, message: str = "", *optional: any) -> None:
        pre = f"{cls.__get_time()}{Color.RED}{cls.__get_pattern()}{cls.__get_caller()}"
        cls.__show_message(cls.__check_file_output(), pre, message, *optional)

    @classmethod
    def exception(cls, message: str = "", *optional: any) -> None:
        pre = f"{cls.__get_time()}{Color.RED}{cls.__get_pattern()}{cls.__get_caller()}"
        cls.__show_message(cls.__check_file_output(), pre, message, *optional)

    @classmethod
    def fatal(cls, message: str = "", *optional: any) -> None:
        pre = f"{cls.__get_time()}{Color.RED}{Color.BOLD}{cls.__get_pattern()}{cls.__get_caller()}"
        cls.__show_message(cls.__check_file_output(), pre, message, *optional)
        raise SystemExit

    # debug, wait

    @classmethod
    def debug(cls, message: str = "", *optional: any) -> None:
        if cls.settings["debug_mode"] and not cls.settings["reduced_mode"]:
            pre = f"{cls.__get_time()}{cls.__get_pattern()}{cls.__get_caller()}"
            cls.__show_message(cls.__check_file_output(), pre, message, *optional)

    @classmethod
    def wait(cls, message: str = "", *optional: any) -> None:
        if cls.settings["debug_mode"]:
            pre = f"{cls.__get_time()}{cls.__get_pattern()}{cls.__get_caller()}"
            cls.__show_message(cls.__check_file_output(), pre, message, *optional)
            try:
                print(f"{Color.RED}{Color.BOLD} >>> Press any key to continue or ESC to exit <<< {Color.RESET}", end="", flush=True)

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
    def __show_message(cls, file_output: bool, pre: str, message: str, *optional: any) -> None:
        extra = ""
        for opt in optional:
            extra += " > " + str(opt)

        text = f"{pre}{message}{extra}"
        text_no_tabs = text.replace("\t", " ")

        if file_output:
            if cls.csv:
                cls.messages.append(remove_colors(text))
            else:
                cls.messages.append(remove_colors(text_no_tabs))

        # https://docs.python.org/3/library/io.html#io.IOBase.isatty

        def is_redirected(stream):
            return not hasattr(stream, "isatty") or not stream.isatty()

        if not cls.settings["color"] or is_redirected(sys.stdout):
            text_no_tabs = remove_colors(text_no_tabs)

        # https://docs.python.org/3/library/sys.html#sys.displayhook

        bytes = (text_no_tabs + "\n").encode("utf-8", "backslashreplace")
        if hasattr(sys.stdout, "buffer"):
            sys.stdout.buffer.write(bytes)
        else:
            text = bytes.decode("utf-8", "strict")
            sys.stdout.write(text)

    @classmethod
    def __get_time(cls) -> str:
        if cls.settings["show_timestamp"]:
            try:
                timezone = ZoneInfo(cls.settings["time_zone"])
                curr_time = datetime.now().astimezone(timezone).strftime("%H:%M:%S.%f")[:-3]
                return f"{Color.BLUE}{curr_time}{Color.RESET}\t"

            # "tzdata" not installed

            except ZoneInfoNotFoundError:
                curr_time = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                return f"{Color.BLACK}{curr_time}{Color.RESET}\t"

        return ""

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
    def __check_file_output(cls) -> bool:
        trace_type = inspect.currentframe().f_back.f_code.co_name
        return trace_type in list(cls.pattern)

    @staticmethod
    def __get_pattern() -> str:
        trace_type = inspect.currentframe().f_back.f_code.co_name
        if trace_type in pattern:
            return pattern[trace_type]
        else:
            return pattern["clear"]

#######################

class ProcessLog:
    def __init__(self):
        self.log = []

    def add(self, info):
        self.log.append(info)

    def get(self):
        return self.log
