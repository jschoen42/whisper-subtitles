"""
    © Jürgen Schoenemeyer, 03.04.2025 20:50

    src/utils/decorator.py

    PUBLIC:
     - @duration(text: str=None, rounds: int=1)
     - @deprecated(message: str="")
     - @retry_exception(text: str="", exception=Exception, delay: int|float=1, retries: int=5)

    PRIVATE:
     - def get_args_values(func: Callable, *args: Any, **kwargs: Any) -> Tuple[List, Dict]:
     - def replace_arguments(match: Match, func_name: str, *args: Any, **kwargs: Any) -> str:
"""
from __future__ import annotations

import contextlib
import functools
import inspect
import re
import time

from inspect import BoundArguments, Signature
from typing import TYPE_CHECKING, Any, Dict, Generator, List, Match, Tuple

from utils.trace import Color, Trace

if TYPE_CHECKING:
    from collections.abc import Callable

""" Decorator '@my_decorator'

def my_decorator(func: Callable) -> Callable:
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:

        # before ...

        result = func(*args, **kwargs)

        # after ...

        return result
    return wrapper
"""

""" Decorator Factory '@my_decorator(params)'

def my_decorator(...) -> Callable:
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

""" Decorator '@my_decorator' + Decorator Factory: '@my_decorator(params)'

# https://calmcode.io/course/decorators/optional-inputs

def my_decorator(function=None, *, ...) -> Callable:
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:

            # before ...

            result = func(*args, **kwargs)

            # after ...

            return result
        return wrapper

    if callable(function):
        return decorator(function) # Decorator
    else:
        return decorator           # Decorator Factory
"""

# @duration    <- there are sometimes (?) problems with the function parameter and mypy, PyRight, Pylance
# @duration()  <- no problems
# @duration("")
# @duration("{__name__} 3: {0} {1} {2}")
# @duration("{__name__} 2: {name} {number} {type}")
# @duration("{__name__} 1: {0|name} {1|number} {2|type}", rounds=1)
# @duration(text="{__name__} 0: {0} {1} {2}", rounds=1)

def duration(special: Callable[[Any], Any] | str | None = None, *, text: str | None = None, rounds: int=1) -> Callable[[Any], Any]:
    def decorator(func: Callable[[Any], Any]) -> Callable[[Any], Any]:
        @functools.wraps(wrapped=func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:

            # get all input args & kwargs of the decorated function
            args_values, kwargs_values = get_args_values(func, *args, **kwargs)

            # before
            start_time = time.perf_counter()

            # decorated function
            result = func(*args, **kwargs)

            # after
            total_time = (time.perf_counter() - start_time) / rounds

            if isinstance(special, str): # text as arg
                pretext = special

            elif text is None:           # text as kwarg
                pretext = func.__name__
            else:
                pretext = text

            # replace arg, kwarg: {0} or {0|name} or {0|name} or {__name__}
            # args_values: ['Max', 99, False], kwargs_values: {'name': 'Max', 'number': 99, 'type': False}

            def replace(match: Match[str]) -> str:
                return replace_argument_values(match, func.__name__, args_values, kwargs_values)

            pattern = r"\{(.*?)\}"
            pretext = re.sub(pattern, replace, pretext)

            duration_text = f"{Color.GREEN}{Color.BOLD}{total_time:.3f} sec{Color.RESET}"
            if pretext == "":
                Trace.decorator(f"{duration_text}", path="duration")
            else:
                Trace.decorator(f"{pretext}: {duration_text}", path="duration")

            return result
        return wrapper

    if callable(special):
        return decorator(special) # @duration
    else:
        return decorator          # @duration(...)


# @deprecated
# @deprecated()
# @deprecated("licence does not fit")
# @deprecated(message="licence does not fit")

def deprecated(special: Callable[[Any], Any] | str | None = None, *, message: str | None = None) -> Callable[[Any], Any]:
    def decorator(func: Callable[[Any], Any]) -> Callable[[Any], Any]:
        @functools.wraps(wrapped=func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:

            text = ""
            if isinstance(special, str): # message as arg
                text = special

            elif message is not None:    # message as kwarg
                text = message

            # before ...

            if text == "":
                Trace.decorator(f"{Color.RED}'{func.__name__}' is deprecated{Color.RESET}", path="deprecated")
            else:
                Trace.decorator(f"{Color.RED}'{func.__name__}' is deprecated ({text}){Color.RESET}", path="deprecated")

            result = func(*args, **kwargs)

            # after ...

            return result
        return wrapper

    if callable(special):
        return decorator(func=special) # @deprecated
    else:
        return decorator          # @deprecated(...

"""
def deprecated(message: str="") -> Callable:
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:

            # before ...

            if message == "":
                Trace.decorator(f"{Color.RED}'{func.__name__}' is deprecated{Color.RESET}", path="deprecated")
            else:
                Trace.decorator(f"{Color.RED}'{func.__name__}' is deprecated ({message}){Color.RESET}", path="deprecated")

            result = func(*args, **kwargs)

            # after ...

            return result
        return wrapper
    return decorator
"""


# @retry_exception(exception=ValueError)
# @retry_exception("error limit '{0}'", exception=ValueError)
# @retry_exception("ttx => font '{0}'", exception=ValueError, delay=2.5, retries=10)

def retry_exception(text: str | None = None, exception: type[BaseException] = Exception, delay: float = 1, retries: int = 5) -> Callable[[Any], Any]:
    def decorator(func: Callable[[Any], Any]) -> Callable[[Any], Any]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:

            # get all input args & kwargs of the decorated function
            args_values, kwargs_values = get_args_values(func, *args, **kwargs)

            if text is None:
                pretext = func.__name__
            else:
                def replace(match: Match[str]) -> str:
                    return replace_argument_values(match, func.__name__, args_values, kwargs_values)

                pattern = r"\{(.*?)\}"
                pretext = re.sub(pattern, replace, text)

            attempts = 0
            while attempts < retries:
                try:
                    return func(*args, **kwargs)
                except exception as _err:
                    attempts += 1
                    attempts_text = f"{Color.RED}{Color.BOLD}failed ({attempts}/{retries}){Color.RESET}"
                    if pretext == "":
                        Trace.decorator(f"{attempts_text}", path="retry")
                    else:
                        Trace.decorator(f"{pretext}: {attempts_text}", path="retry")

                    time.sleep(delay)

            raise exception
        return wrapper
    return decorator

# get args and kwargs values -> default values are considered

def get_args_values(func: Callable[[Any], Any], *args: Any, **kwargs: Any) -> Tuple[List[Any], Dict[Any, Any]]:
    sig: Signature = inspect.signature(func)
    bound_args: BoundArguments = sig.bind_partial(*args, **kwargs)
    bound_args.apply_defaults()

    args_values = []
    kwargs_values = {}
    for name, value in bound_args.arguments.items():
        args_values.append(value)
        kwargs_values[name] = value

    return args_values, kwargs_values

# @duration("{__name__} 1: {0|name} {1|number} {2|type}"
# args_values: ['Max', 99, False], kwargs_values: {'name': 'Max', 'number': 99, 'type': False}

def replace_argument_values(match: Match[str], func_name: str, args_values: List[Any], kwargs_values: Dict[Any, Any]) -> str:
    arguments = match.group(1)

    if arguments == "__name__":
        return(func_name)

    for argument in arguments.split("|"):
        if argument.isnumeric():
            # args_values: {0} -> args_values[0]
            pos = int(argument)
            if pos < len(args_values):
                return str(args_values[pos])

        # kwargs_values: {type} -> kwargs_values["type"]

        elif argument in kwargs_values:
            return str(kwargs_values.get(argument))

    return ""

# https://www.youtube.com/watch?v=xI4TJyd8FGk&t=860s
#
# @type_check(int, int)
#  - not for kwargs !
#  - not using the existing annotation !

def type_check(*expected_types: type) -> Callable[[Any], Any]:
    def decorator(func: Callable[[Any], Any]) -> Callable[[Any], Any]:
        @functools.wraps(wrapped=func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            result = func(*args, **kwargs)

            for arg, expected_type in zip(args, expected_types, strict=False):
                if not isinstance(arg, expected_type):
                    Trace.error("TypeError - expected {expected_type}, but got {type}")

            return result
        return wrapper
    return decorator

###### decorator with ContextManager

# https://www.youtube.com/watch?v=_QXlbwRmqgI&t=260s

# BUT: arg, *kwarg not available

@contextlib.contextmanager
def duration_cm(name: str) -> Generator[None, None, None]:  # noqa: UP043
    start_time = time.perf_counter()
    try:
        yield
    finally:
        end_time = time.perf_counter()
        total_time = (end_time - start_time)

        text = f"{Color.GREEN}{Color.BOLD}{total_time:.3f} sec{Color.RESET}"
        Trace.decorator(f"{name}: {text}", path="duration")
