"""
    (c) Jürgen Schoenemeyer, 16.11.2024

    PUBLIC:
    camel_to_snake(name: str) -> str
    snake_to_camel(name: str) -> str

    pascal_to_snake(name: str) -> str
    snake_to_pascal(name: str) -> str

"""

import re

# https://stackoverflow.com/questions/17156078/converting-identifier-naming-between-camelcase-and-snakes-during-json-seria#answer-17156414

# camelCase <-> snake_case

def camel_to_snake(name: str) -> str:
    """  convert 'camelCase' to 'snake_case' """

    pattern  = re.compile(r"([A-Z])")
    return pattern.sub(lambda x: "_" + x.group(1).lower(), name)

def snake_to_camel(name: str) -> str:
    """  convert 'camel_case' to 'camelCase' """

    pattern  = re.compile(r"_([a-z])")
    return pattern.sub(lambda x: x.group(1).upper(), name)

# PascalCase <-> snake_case

def pascal_to_snake(name: str) -> str:
    """  convert 'PascalCase' to 'snake_case' """

    pattern = re.compile(r"(?<!^)(?=[A-Z])")
    return pattern.sub("_", name).lower()

def snake_to_pascal(name: str) -> str:
    """  convert 'snake_case' to 'PascalCase' """

    pattern = re.compile(r"(^|_)([a-z])")
    return pattern.sub(lambda x: x.group(2).upper(), name)

""" toDo -> files.py
import json

def convert_load(*args, **kwargs):
    json_obj = json.load(*args, **kwargs)
    return convert_json(json_obj, camel_to_snake)

def convert_dump(*args, **kwargs):
    args = (convert_json(args[0], snake_to_camel),) + args[1:]
    json.dump(*args, **kwargs)
"""


# https://docs.python.org/3/library/stdtypes.html#str.title
#
# "they're bill's friends from the UK".title()   -> "They'Re Bill'S Friends From The Uk"
# to_title("they're bill's friends from the UK") -> "They're Bill's Friends From The Uk"

def to_title(text: str) -> str:
    """  patch 'apostroph' for str.title() """

    pattern = re.compile(r"[A-Za-z]+('[A-Za-z]+)?")
    return pattern.sub(lambda mo: mo.group(0).capitalize(), text)



