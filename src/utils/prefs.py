"""
    © Jürgen Schoenemeyer, 03.04.2025 20:50

    src/utils/prefs.py

    PUBLIC:
    static class Prefs:
      - Prefs.init(pref_path = None, pref_prefix = None) -> None
      - Prefs.load(pref_name: str) -> bool
      - Prefs.get(key_path: str) -> Any

    PRIVATE:
     - merge_dicts(a: Dict, b: Dict) -> Dict
     - build_tree(tree: List, in_key: str, value: str) -> Dict
"""
from __future__ import annotations

import json
import re

from json import JSONDecodeError
from pathlib import Path
from typing import Any, ClassVar, Dict, List, Tuple

import yaml

from utils.globals import BASE_PATH
from utils.trace import Trace

class Prefs:
    pref_path: Path = BASE_PATH / "prefs"
    pref_prefix: str = ""
    data: ClassVar[Dict[Any, Any]] = {}

    @classmethod
    def init(cls, pref_path: Path | str | None = None, pref_prefix: str | None = None) -> None:
        if pref_path is not None:
            cls.pref_path = BASE_PATH / pref_path
        if pref_prefix is not None:
            cls.pref_prefix = pref_prefix
        cls.data = {}

    @classmethod
    def load(cls, pref_name: str) -> bool:
        ext = Path(pref_name).suffix
        if ext not in [".yaml", ".yml"]:
            Trace.error(f"'{pref_name}' not supported (use .yaml or .yml)")
            return False

        pref_name = cls.pref_prefix + pref_name
        if not Path(cls.pref_path, pref_name).is_file():
            Trace.error(f"pref not found '{cls.pref_path}\\{pref_name}'")
            return False
        try:
            with (cls.pref_path / pref_name).open(mode="r", encoding="utf-8") as file:
                data = yaml.safe_load(file)

            cls.data = dict(merge_dicts(cls.data, data))
            # cls.data = merge(dict(cls.data), data) # -> Exception: Conflict at trainingCompany

        except yaml.YAMLError as e:
            Trace.fatal(f"YAMLError '{pref_name}':\n{e}")
            return False

        except OSError as e:
            Trace.error(f"{pref_name}: {e}")
            return False

        return True

    @classmethod
    def get_all(cls) -> Dict[Any, Any]:
        return cls.data

    @classmethod
    def get(cls, key_path: str, default:Any = None) -> Any:

        def get_pref_key(key_path: str) -> Any: # key_path = "one.two.three" -
            keys: list[str] = key_path.split(".")

            data = cls.data

            for key in keys:
                if data is None or key not in data:
                    if default is None:
                        Trace.fatal(f"unknown pref '{key_path}'")

                    Trace.info(f"unknown pref '{key_path}' -> {default}")
                    return default

                data = data[key]

            return data

        result = get_pref_key(key_path)

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
        except JSONDecodeError as e:
            Trace.error(f"json error: {key_path} -> {tmp} ({e})")
            ret = ""

        return ret


def get_pref_special(pref_path: Path, pref_prexix: str, pref_name: str, key: str) -> str:
    try:
        path = pref_path / pref_prexix / (pref_name + ".yaml")
        with path.open(mode="r", encoding="utf-8") as file:
            pref = yaml.safe_load(file)

    except yaml.YAMLError as e:
        Trace.fatal(f"YAMLError '{pref_name}':\n{e}")
        return ""

    except OSError as e:
        Trace.error(f"{beautify_path(str(e))}")
        return ""

    if key in pref:
        return str(pref[key])
    else:
        Trace.error(f"unknown pref: {pref_name} / {key}")
        return ""

def read_pref(pref_path: Path, pref_name: str) -> Tuple[bool, Dict[Any, Any]]:
    try:
        with (pref_path / pref_name).open(mode="r", encoding="utf-8") as file:
            data = yaml.safe_load(file)

    except yaml.YAMLError as e:
        Trace.fatal(f"YAMLError '{pref_name}':\n{e}")
        return True, {}

    except OSError as e:
        Trace.error(f"{beautify_path(str(e))}")
        return True, {}

    return False, data

def beautify_path(path: Path | str) -> str:
    return str(path).replace("\\\\", "/")

# https://stackoverflow.com/questions/7204805/deep-merge-dictionaries-of-dictionaries-in-python?page=1&tab=scoredesc#answer-7205672

def merge_dicts(a: Dict[Any, Any], b: Dict[Any, Any]) -> Any:
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

# def merge(a: Dict[Any, Any], b: Dict[Any, Any], path: List[str] = []) -> Any:
#     for key in b:
#         if key in a:
#             if isinstance(a[key], dict) and isinstance(b[key], dict):
#                 merge(a[key], b[key], path + [str(key)])
#             elif a[key] != b[key]:
#                 raise Exception("Conflict at " + ".".join(path + [str(key)]))
#         else:
#             a[key] = b[key]
#     return a

def merge(a: Dict[Any, Any], b: Dict[Any, Any], path: List[str] | None = None) -> Any:
    if path is None:
        path = []

    for key, value in b.items():
        if key in a:
            if isinstance(a[key], dict) and isinstance(value, dict):
                merge(a[key], b[key], [*path, str(key)])
            elif a[key] != b[key]:
                raise Exception("Conflict at " + ".".join([*path, str(key)]))
        else:
            a[key] = b[key]
    return a

def build_tree(tree: List[str], in_key: str, value: str) -> Dict[str, Any]:
    if tree:
        return {tree[0]: build_tree(tree[1:], in_key, value)}

    return { in_key: value }
