"""
    (c) Jürgen Schoenemeyer, 10.12.2024

    @duration(pre_text: str = "", rounds: int = 1)

    @duration("argon2 (20 rounds)", 20) # test with 20 rounds => average duration for a round

    @duration("ttx => font '{0}'")      # 0    -> args
    @duration("ttx => font '{type}'")   # type -> kwargs

"""

import contextlib
import time
import re

from typing import Generator
from collections.abc import Callable

from src.utils.trace import Trace, Color

def duration(pre_text: str = "", rounds: int = 1) -> Callable:
    def decorator(func: Callable) -> Callable:
        def wrapper(*args: any, **kwargs: any) -> any:
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



# https://www.youtube.com/watch?v=_QXlbwRmqgI&t=260s

# BUT: arg, *kwarg not available

@contextlib.contextmanager
def timeit(name: str) -> Generator[None, None, None]:
    start_time = time.perf_counter()
    try:
        yield
    finally:
        end_time = time.perf_counter()
        total_time = (end_time - start_time)

        text = f"{Color.GREEN}{Color.BOLD}{total_time:.3f} sec{Color.RESET}"
        Trace.time(f"{name}: {text}")
