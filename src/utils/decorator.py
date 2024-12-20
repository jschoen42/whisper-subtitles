"""
    © Jürgen Schoenemeyer, 20.12.2024

    PUBLIC:
     - @duration(pre_text: str="", rounds: int=1)
     - @deprecation(message: str="")

     - @retry_exception(pre_text: str="", exception=Exception, delay: int|float=1, retries: int=5)

    PRIVAT:
      - def replace_arguments(match: Match, func_name: str, *args, **kwargs) -> str:
"""

import contextlib
import time
import re
import functools

from typing import Any, Generator, Match
from collections.abc import Callable

from utils.trace import Trace, Color

""" Decorator: @decorator

def my_decorator(func: Callable) -> Callable:
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:

        # before ...

        result = func(*args, **kwargs)

        # after ...

        return result
    return wrapper
"""

""" Decorator Factory: @decorator( params )

def my_decorator( ... ) -> Callable:
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:

            # before ...

            result = func(*args, **kwargs)

            # after ...

            return result
        return wrapper
    return decorator
"""
# @duration()
# @duration("ttx => font '{0}'")      # 0    -> args
# @duration("ttx => font '{type}'")   # type -> kwargs

# @duration("argon2 (20 rounds)", 20) # test with 20 rounds => average duration for a round

def duration(pre_text: str=None, rounds: int=1) -> Callable:
    def decorator(func: Callable) -> Callable:
        @functools.wraps(replace_arguments)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            start_time = time.perf_counter()

            result = func(*args, **kwargs)

            end_time = time.perf_counter()
            total_time = (end_time - start_time) / rounds

            if pre_text is None:
                pretext = func.__name__
            else:
                def replace(match: Match) -> str:
                    return replace_arguments( match, func.__name__, *args, **kwargs )

                pattern = r"\{(.*?)\}"
                pretext = re.sub(pattern, replace, pre_text)

            text = f"{Color.GREEN}{Color.BOLD}{total_time:.3f} sec{Color.RESET}"
            if pretext == "":
                Trace.custom(f"{text}", path="duration")
            else:
                Trace.custom(f"{pretext}: {text}", path="duration")

            return result
        return wrapper
    return decorator

# @deprecation()
# @deprecation("licence does not fit")

def deprecation(message: str="") -> Callable:
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:

            # before ...

            if message == "":
                Trace.custom(f"{Color.RED}'{func.__name__}' is deprecated{Color.RESET}", path="deprecation")
            else:
                Trace.custom(f"{Color.RED}'{func.__name__}' is deprecated ({message}){Color.RESET}", path="deprecation")

            result = func(*args, **kwargs)

            # after ...

            return result
        return wrapper
    return decorator

# @retry_exception(exception=ValueError)
# @retry_exception("error limit '{0}'", exception=ValueError)
# @retry_exception("ttx => font '{0}'", exception=ValueError, delay=2.5, retries=10)

def retry_exception(pre_text: str=None, exception=Exception, delay: int|float=1, retries: int=5) -> Callable:
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:

            if pre_text is None:
                pretext = func.__name__
            else:
                def replace(match: Match) -> str:
                    return replace_arguments( match, func.__name__, *args, **kwargs )

                pattern = r"\{(.*?)\}"
                pretext = re.sub(pattern, replace, pre_text)

            attempts = 0
            while attempts < retries:
                try:
                    return func(*args, **kwargs)
                except exception as _err:
                    attempts += 1
                    text = f"{Color.RED}{Color.BOLD}failed ({attempts}/{retries}){Color.RESET}"
                    if pretext == "":
                        Trace.custom(f"{text}", path="retry")
                    else:
                        Trace.custom(f"{pretext}: {text}", path="retry")

                    time.sleep(delay)

            raise exception
        return wrapper
    return decorator

# https://www.youtube.com/watch?v=xI4TJyd8FGk&t=860s
#
# @type_check(int, int)
#  - not for kwargs !
#  - not using the existing annotation !

def type_check(*expected_types) -> Callable:
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            result = func(*args, **kwargs)

            for arg, expected_type in zip(args, expected_types):
                if not isinstance(arg, expected_type):
                    Trace.error( "TypeError - expected {expected_type}, but got {type}" )

            return result
        return wrapper
    return decorator


###### decorator with ContextManager

# https://www.youtube.com/watch?v=_QXlbwRmqgI&t=260s

# BUT: arg, *kwarg not available

@contextlib.contextmanager
def duration_cm(name: str) -> Generator[None, None, None]:
    start_time = time.perf_counter()
    try:
        yield
    finally:
        end_time = time.perf_counter()
        total_time = (end_time - start_time)

        text = f"{Color.GREEN}{Color.BOLD}{total_time:.3f} sec{Color.RESET}"
        Trace.custom(f"{name}: {text}", path="duration")


# helper

def replace_arguments(match: Match, func_name: str, *args, **kwargs) -> str:
    argument = match.group(1)

    if argument == "__name__":
        return( func_name )

    elif argument.isnumeric():
        # args
        pos = int(argument)
        if pos < len(args):
            return str(args[pos])  # {0} -> args[0]
        else:
            Trace.error(f"arg '{pos}' does not exist")
            return f"<'{pos}' not exist>"

    else:
        # kwargs
        if argument in kwargs:
            return str(kwargs.get(argument)) # {type} -> kwargs["type"]
        else:
            Trace.error(f"kwarg '{argument}' does not exist")
            return f"<'{argument}' not exist>"
