"""
    © Jürgen Schoenemeyer, 21.12.2024

    PUBLIC:
    class Prefs:
      - init(cls, pref_path = None, pref_prefix = None ) -> None
      - load(cls, pref_name: str) -> bool
      - get(cls, key_path: str) -> Any

    merge_dicts(a: dict, b: dict) -> dict
    build_tree(tree: list, in_key: str, value: str) -> dict
"""

import json
import re

from json    import JSONDecodeError
from pathlib import Path
from typing  import Any, Tuple

import yaml

from utils.globals import BASE_PATH
from utils.trace   import Trace
from utils.file    import beautify_path

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
    def load(cls, pref_name: str) -> bool:
        ext = Path(pref_name).suffix
        if ext not in [".yaml", ".yml"]:
            Trace.error(f"'{ext}' not supported")
            return False

        pref_name = cls.pref_prefix + pref_name
        if not Path(cls.pref_path, pref_name).is_file():
            Trace.error(f"pref not found '{cls.pref_path}\\{pref_name}'")
            return False
        try:
            with open( Path(cls.pref_path, pref_name), "r", encoding="utf-8") as file:
                data = yaml.safe_load(file)

            cls.data = dict(merge_dicts(cls.data, data))
            # cls.data = merge(dict(cls.data), data) # -> Exception: Conflict at trainingCompany

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
    def get(cls, key: str) -> Any:

        def get_pref_key(key_path: str) -> Any:
            keys = key_path.split(".")

            data = cls.data
            for key in keys:
                if key in data:
                    data = data[key]
                else:
                    Trace.fatal(f"unknown pref: {key}")
            return data

        result = get_pref_key(key)

        # pref.yaml
        #   filename:  'data.xlsx'
        #   filepaths: ['..\result\{{filename}}']
        #
        # -> filepaths = ['..\result\data.xlsx']

        # dict -> text -> replace -> dict

        tmp = json.dumps(result)

        pattern = r"\{\{([^\}]+)\}\}" # '{{ ... }}'
        replace = re.findall(pattern, tmp)
        if len(replace)==0:
            return result

        for entry in replace:
            tmp = tmp.replace("{{" + entry + "}}", get_pref_key(entry))

        try:
            ret = json.loads(tmp)
        except JSONDecodeError as err:
            Trace.error(f"json error: {key} -> {tmp} ({err})")
            ret = ""

        return ret


def get_pref_special(pref_path: Path, pref_prexix, pref_name: str, key: str) -> str:
    try:
        with open(Path(pref_path, pref_prexix + pref_name + ".yaml"), "r", encoding="utf-8") as file:
            pref = yaml.safe_load(file)
    except OSError as err:
        Trace.error(f"{beautify_path(err)}")
        return ""

    if key in pref:
        return pref[key]
    else:
        Trace.error(f"unknown pref: {pref_name} / {key}")
        return ""

def read_pref( pref_path: Path, pref_name: str ) -> Tuple[bool, dict]:
    try:
        with open( Path(pref_path, pref_name), "r", encoding="utf-8") as file:
            data = yaml.safe_load(file)

        # Trace.wait( f"{pref_name}: {json.dumps(data, sort_keys=True, indent=2)}" )
        return False, data

    except OSError as err:
        Trace.error( f"{beautify_path(err)}" )
        return True, {}

# https://stackoverflow.com/questions/7204805/deep-merge-dictionaries-of-dictionaries-in-python?page=1&tab=scoredesc#answer-7205672

def merge_dicts(a: dict, b: dict) -> Any:
    for k in set(a.keys()).union(b.keys()):
        if k in a and k in b:
            if isinstance(a[k], dict) and isinstance(b[k], dict):
                yield (k, dict(merge_dicts(a[k], b[k])))
            else:
                # If one of the values is not a dict, you can't continue merging it.
                # Value from second dict overrides one in first and we move on.
                yield (k, b[k])
                # Alternatively, replace this with exception raiser to alert you of value conflicts
        elif k in a:
            yield (k, a[k])
        else:
            yield (k, b[k])

# https://stackoverflow.com/questions/7204805/deep-merge-dictionaries-of-dictionaries-in-python?page=1&tab=scoredesc#answer-7205107

def merge(a: dict, b: dict, path=[]) -> Any:
    for key in b:
        if key in a:
            if isinstance(a[key], dict) and isinstance(b[key], dict):
                merge(a[key], b[key], path + [str(key)])
            elif a[key] != b[key]:
                raise Exception("Conflict at " + ".".join(path + [str(key)]))
        else:
            a[key] = b[key]
    return a

def build_tree(tree: list, in_key: str, value: str) -> dict:
    if tree:
        return {tree[0]: build_tree(tree[1:], in_key, value)}

    return { in_key: value }
