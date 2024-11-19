"""
    (c) Jürgen Schoenemeyer, 02.11.2024

    PUBLIC:
    class Prefs:
        init(cls, pref_path = None, pref_prefix = None ) -> None
        read(cls, pref_name: str) -> bool
        get(cls, key_path: str, default: Any = None) -> Any

    merge_dicts(dict1: dict, dict2: dict) -> dict
    build_tree(tree: list, in_key: str, value: str) -> dict
"""

from typing import Any
from pathlib import Path

import yaml

from src.utils.trace import Trace, BASE_PATH

class Prefs:
    pref_path   = BASE_PATH / "prefs"
    pref_prefix = ""
    data = {}

    @classmethod
    def init(cls, pref_path = None, pref_prefix = None ) -> None:
        if pref_path is not None:
            cls.pref_path = BASE_PATH / pref_path
        if pref_prefix is not None:
            cls.pref_prefix = pref_prefix
        cls.data = {}

    @classmethod
    def read(cls, pref_name: str) -> bool:
        ext = Path(pref_name).suffix
        if ext not in [".yaml", ".yml"]:
            Trace.error(f"'{ext}' not supported")
            return False

        pref_name = cls.pref_prefix + pref_name
        if not Path(cls.pref_path, pref_name).is_file():
            Trace.error(f"pref not found '{pref_name}'")
            return False
        try:
            with open( Path(cls.pref_path, pref_name), "r", encoding="utf-8") as file:
                data = yaml.safe_load(file)

            cls.data = dict(merge_dicts(cls.data, data))

        except yaml.scanner.ScannerError as err:
            Trace.fatal(f"{pref_name}:\n{err}")

        except OSError as err:
            Trace.error(f"{pref_name}: {err}")
            return False

        return True

    @classmethod
    def get_all(cls) -> dict:
        return cls.data

    @classmethod
    def get(cls, key_path: str, default: Any = None) -> Any:
        keys = key_path.split(".")

        data = cls.data
        for key in keys:
            if key in data:
                data = data[key]
            else:
                if default is None:
                    Trace.fatal(f"unknown key '{key_path}'")
                else:
                    Trace.error(f"unknown key '{key_path}' -> default value '{default}'")
                    return default

        return data

# https://stackoverflow.com/questions/7204805/how-to-merge-dictionaries-of-dictionaries

def merge_dicts(dict1: dict, dict2: dict) -> any:
    for k in set(dict1.keys()).union(dict2.keys()):
        if k in dict1 and k in dict2:
            if isinstance(dict1[k], dict) and isinstance(dict2[k], dict):
                yield (k, dict(merge_dicts(dict1[k], dict2[k])))
            else:
                # If one of the values is not a dict, you can't continue merging it.
                # Value from second dict overrides one in first and we move on.
                yield (k, dict2[k])
                # Alternatively, replace this with exception raiser to alert you of value conflicts
        elif k in dict1:
            yield (k, dict1[k])
        else:
            yield (k, dict2[k])

def build_tree(tree: list, in_key: str, value: str) -> dict:
    if tree:
        return {tree[0]: build_tree(tree[1:], in_key, value)}

    return { in_key: value }
