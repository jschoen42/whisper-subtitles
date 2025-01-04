"""
    © Jürgen Schoenemeyer, 04.01.2025

    PUBLIC:
    class Prefs:
      - init(cls, pref_path = None, pref_prefix = None ) -> None
      - load(cls, pref_name: str) -> bool
      - get(cls, key_path: str) -> Any

    merge_dicts(a: Dict, b: Dict) -> Dict
    build_tree(tree: list, in_key: str, value: str) -> Dict
"""

import json
import re

from json    import JSONDecodeError
from pathlib import Path
from typing  import Any, Dict, Tuple

import yaml

from utils.globals import BASE_PATH
from utils.trace   import Trace
from utils.file    import beautify_path

class Prefs:
    pref_path: Path = BASE_PATH / "prefs"
    pref_prefix: str = ""
    data: Dict = {}

    @classmethod
    def init(cls, pref_path: Path | str | None = None, pref_prefix: str | None = None ) -> None:
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

        except yaml.parser.ParserError as err:
            Trace.fatal(f"ParserError '{pref_name}':\n{err}")

        except yaml.scanner.ScannerError as err:
            Trace.fatal(f"ScannerError '{pref_name}':\n{err}")

        except OSError as err:
            Trace.error(f"{pref_name}: {err}")
            return False

        return True

    @classmethod
    def get_all(cls) -> Dict:
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

        # Dict -> text -> replace -> Dict

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


def get_pref_special(pref_path: Path, pref_prexix: str, pref_name: str, key: str) -> str:
    try:
        with open(Path(pref_path, pref_prexix + pref_name + ".yaml"), "r", encoding="utf-8") as file:
            pref = yaml.safe_load(file)
    except OSError as err:
        Trace.error(f"{beautify_path(str(err))}")
        return ""

    if key in pref:
        return pref[key]
    else:
        Trace.error(f"unknown pref: {pref_name} / {key}")
        return ""

def read_pref( pref_path: Path, pref_name: str ) -> Tuple[bool, Dict]:
    try:
        with open( Path(pref_path, pref_name), "r", encoding="utf-8") as file:
            data = yaml.safe_load(file)

        # Trace.wait( f"{pref_name}: {json.dumps(data, sort_keys=True, indent=2)}" )
        return False, data

    except OSError as err:
        Trace.error( f"{beautify_path(str(err))}" )
        return True, {}

# https://stackoverflow.com/questions/7204805/deep-merge-dictionaries-of-dictionaries-in-python?page=1&tab=scoredesc#answer-7205672

def merge_dicts(a: Dict, b: Dict) -> Any:
    for k in set(a.keys()).union(b.keys()):
        if k in a and k in b:
            if isinstance(a[k], Dict) and isinstance(b[k], Dict):
                yield (k, Dict(merge_dicts(a[k], b[k])))
            else:
                # If one of the values is not a Dict, you can't continue merging it.
                # Value from second Dict overrides one in first and we move on.
                yield (k, b[k])
                # Alternatively, replace this with exception raiser to alert you of value conflicts
        elif k in a:
            yield (k, a[k])
        else:
            yield (k, b[k])

# https://stackoverflow.com/questions/7204805/deep-merge-dictionaries-of-dictionaries-in-python?page=1&tab=scoredesc#answer-7205107

def merge(a: Dict, b: Dict, path: list[str] = []) -> Any:
    for key in b:
        if key in a:
            if isinstance(a[key], Dict) and isinstance(b[key], Dict):
                merge(a[key], b[key], path + [str(key)])
            elif a[key] != b[key]:
                raise Exception("Conflict at " + ".".join(path + [str(key)]))
        else:
            a[key] = b[key]
    return a

def build_tree(tree: list, in_key: str, value: str) -> Dict:
    if tree:
        return {tree[0]: build_tree(tree[1:], in_key, value)}

    return { in_key: value }
