"""
    (c) Jürgen Schoenemeyer, 06.12.2024

    error channel -> rustedpy/result

    PUBLIC:
    result = get_timestamp(filepath: Path | str) -> Result[float, str]:
    result = set_timestamp(filepath: Path | str, timestamp: float) -> Result[(), str]:

    result = get_files_dirs(path: str, extensions: list) -> Result[tuple[list, list], str]:

    result = read_file(filepath: Path | str, encoding: str="utf-8" ) -> Result[any, str]
    result = write_file(filepath: Path | str, data: any, encoding: str="utf-8", create_dir: bool = True, show_message: bool=True) -> Result[str, str]:

    from result import is_err, is_ok

    if is_err(result):
        Trace.error(f"Error: {result.err_value}")
    else:
        data = result.ok_value

    supported types
     - .txt
     - .json (json or orjson)
     - .xml (minidom or xml.etree.ElementTree)

"""

import os
import sys

from datetime import datetime
from pathlib import Path

from xml.dom import minidom
import xml.etree.ElementTree as ET

try:
    import xmltodict
except ModuleNotFoundError:
    pass

try:
    import dicttoxml
except ModuleNotFoundError:
    pass

try:
    import orjson
except ModuleNotFoundError:
    import json

from result import Result, Ok, Err

from src.utils.trace import Trace

TIMESTAMP = "%Y-%m-%d_%H-%M-%S"

def get_timestamp(filepath: Path | str) -> Result[float, str]:
    """
    ### get timestamp of a file

    #### Arguments
     - filepath: Path or str

    #### Return [rustedpy]
     - Ok: timestamp as float
     - Err: errortext as str
    """

    if not filepath.exists():
        err = f"'{filepath}' does not exist"
        Trace.debug(f"{err}")
        return Err(err)

    try:
        ret = os.path.getmtime(Path(filepath))
    except OSError as err:
        Trace.debug(f"{err}")
        return Err(f"{err}")

    return Ok(ret)

def set_timestamp(filepath: Path | str, timestamp: int|float) -> Result[str, str]:
    """
    ### set timestamp of a file

    #### Arguments
     - filepath: Path or str
     - timestamp: float

    #### Return [rustedpy]
     - Ok: -
     - Err: errortext as str
    """

    filepath = Path(filepath)

    if not filepath.exists():
        err = f"'{filepath}' does not exist"
        Trace.debug(f"{err}")
        return Err(err)

    try:
        os.utime(Path(filepath), times = (timestamp, timestamp)) # atime and mtime
    except OSError as err:
        Trace.debug(f"{err}")
        return Err(f"{err}")

    return Ok("")

# dir listing -> list of files and dirs

def get_files_dirs(path: str, extensions: list) -> Result[tuple[list, list], str]:
    files: list = []
    dirs = []
    try:
        for filename in os.listdir(path):
            filepath = os.path.join(path, filename)

            if os.path.isfile(filepath):
                for extention in extensions:
                    if "." + extention in filename:
                        files.append(filename)
                        break
            else:
                dirs.append(filename)

    except OSError as err:
        Trace.error(f"{err}")
        return Err(f"{err}")

    return Ok(files, dirs)

def read_file(filepath: Path | str, encoding: str="utf-8") -> Result[any, str]:
    """
    ### read file (text, json, xml)

    #### Arguments
     - filepath: Path or str  - supported suffixes: '.txt', '.json', '.xml'
     - encoding: str - used only for '.txt'

    #### Return [rustedpy]
     - Ok: data as any
     - Err: errortext as str
    ---
    #### Infos
     - using orjson (if installed) for '.json' files
     - auto convert (xml <-> json)
     - xml used minidom or xml.etree.ElementTree
    """

    filepath = Path(filepath)
    dirpath  = Path(filepath).parent
    filename = Path(filepath).name

    # 1. type check

    suffix  = Path(filename).suffix

    if suffix == ".txt":
        type = "text"

    elif suffix == ".json":
        type = "json"

    elif suffix == ".xml":
        type = "xml"

    else:
        err = f"Type '{suffix}' is not supported"
        Trace.debug(err)
        return Err(err)

    # 2. directory check

    if not dirpath.exists():
        err = f"DirNotFoundError: '{dirpath}'"
        Trace.debug(err)
        return Err(err)

    # 3. file check + deserialization

    if not filepath.exists():
        err = f"FileNotFoundError: '{filepath}'"
        Trace.debug(err)
        return Err(err)

    try:
        with open(filepath, "r", encoding=encoding) as f:
            text = f.read()
    except OSError as err:
        Trace.debug(f"{err}")
        return Err(f"{err}")

    if type == "text":
        return Ok(text)

    elif type == "json":
        if "orjson" in sys.modules:
            try:
                data = orjson.loads(text)
            except orjson.JSONDecodeError as err:
                err = f"JSONDecodeError: {filepath} => {err}"
                Trace.debug(err)
                return Err(err)
            return Ok(data)
        else:
            try:
                data = json.loads(text)
            except json.JSONDecodeError as err:
                err = f"JSONDecodeError: {filepath} => {err}"
                Trace.debug(err)
                return Err(err)
            return Ok(data)

    elif type == "xml":
        try:
            # data = ET.fromstring(text)
            data = minidom.parseString(text)
        except (TypeError, AttributeError) as err:
            err = f"ParseError: {err}"
            Trace.debug(err)
            return Err(err)
        return Ok(data)


def write_file(filepath: Path | str, data: any, filename_timestamp: bool = False, timestamp: int|float = 0, encoding: str="utf-8", newline: str="\n", create_dir: bool = True, show_message: bool=True) -> Result[str, str]:
    """
    ### write file (text, json, xml)

    #### Arguments
     - filepath: Path or str - supported suffixes: '.txt', '.json', '.xml'
     - filename_timestamp: bool - add timestamp to filename
     - timestamp: float - timestamp in sec
     - encoding: str - used only for '.txt'
     - newline: str - "\\n" or "\\r\\n"
     - create_dir: bool - create directory if not exists (default: True)

    #### Returns [rustedpy]
     - Ok: -
     - Err: errortext as str
    ----
    #### Infos
     - using orjson (if installed) for '.json' files
     - auto convert (xml <-> json)
     - xml used minidom or xml.etree.ElementTree
    """

    filepath = Path(filepath)
    dirpath  = Path(filepath).parent
    filename = Path(filepath).name

    suffix = Path(filename).suffix
    stem = Path(filename).stem

    if filename_timestamp:
        filename = f"{stem}_{datetime.now().strftime(TIMESTAMP)}{suffix}"

    # 1. type check + serialization

    if suffix in [".txt", ".csv"]:
        if not isinstance(data, str):
            err = f'write_file \'{suffix}\': "{str(data)[:50]} …" is not a string'
            Trace.debug(err)
            return Err(err)
        else:
            text = data

    elif suffix == ".json":

        # xxl -> json

        if isinstance(data, minidom.Document):
            text = data.toxml()
            data = xmltodict.parse(text)

        elif isinstance(data, ET.Element):
            text = ET.tostring(data, method="xml", xml_declaration=True, encoding="unicode")
            data = xmltodict.parse(text)

        # json -> json

        def serialize_sets(obj):
            if isinstance(obj, set):
                return sorted(obj)

            return obj

        if isinstance(data, dict) or isinstance(data, list):
            try:
                if "orjson" in sys.modules:
                    text = orjson.dumps(data, default=serialize_sets, option=orjson.OPT_INDENT_2).decode("utf-8")
                else:
                    text = json.dumps(data, default=serialize_sets, indent=2, ensure_ascii=False)
            except TypeError as err:
                Trace.error(f"TypeError: {err}")
                return Err(err)
        else:
            err = f"Type '{type(data)}' is not supported for '{suffix}'"
            Trace.error(err)
            return Err(err)

    elif suffix == ".xml":

        # xml -> xml

        if isinstance(data, minidom.Document):
            text = data.toxml()
            text = text.replace('<?xml version="1.0" ?>', '<?xml version="1.0" encoding="utf-8" standalone="yes"?>\n')

        elif isinstance(data, ET.Element):
            text = ET.tostring(data, method="xml", xml_declaration=True, encoding="unicode")
            text = text.replace("<?xml version='1.0' encoding='utf-8'?>", '<?xml version="1.0" encoding="utf-8" standalone="yes"?>')

        # json -> xml

        elif isinstance(data, dict):
            text = minidom.parseString(dicttoxml(data)).toprettyxml(indent="  ")
            text = text.replace('<?xml version="1.0" ?>', '<?xml version="1.0" encoding="utf-8" standalone="yes"?>')

        else:
            err = f"Type '{type(data)}' is not supported for '{suffix}'"
            Trace.debug(err)
            return Err(err)

    else:
        err = f"Type '{suffix}' is not supported"
        Trace.debug(err)
        return Err(err)

    # 2. directory check

    if not dirpath.exists():
        if create_dir:
            try:
                os.makedirs(dirpath)
                Trace.update(f"'{dirpath}' created")
            except OSError as err:
                Trace.debug(f"{err}")
                return Err(f"{err}")
        else:
            return Err(f"DirNotFoundError: '{dirpath}'")

    # 3. file check

    if filepath.exists():
        try:
            with open(filepath, "r", encoding=encoding) as f:
                text_old = f.read()
        except OSError as err:
            Trace.debug(f"{err}")
            return Err(f"{err}")

        if text == text_old:
            Trace.info(f"'{filepath}' not modified")
            return Ok("")

        try:
            with open(filepath, "w", encoding=encoding) as f:
                f.write(text)
        except OSError as err:
            return Err(f"{err}")

        if show_message:
            Trace.update(f"'{filepath}' updated")

    else:
        try:
            with open(filepath, "w", encoding=encoding, newline=newline) as f:
                f.write(text)
        except OSError as err:
            Trace.debug(f"{err}")
            return Err(f"{err}")

        if show_message:
            Trace.update(f"'{filepath}' created")

    # 4: optional: set file timestamp

    if timestamp > 0:
        try:
            os.utime(filepath, times = (timestamp, timestamp)) # atime and mtime
        except OSError as err:
            Trace.debug(f"{err}")
            return Err(f"timestamp: {err}")

    return Ok("")

def listdir_ext(dirpath: Path | str, extensions: list = None) -> Result[list, str]:
    """
    ### list all files in directory which matches the extentions

    #### Arguments
     - dirpath: Path or str
     - extensions: e.g. str [".zip", ".story", ".xlsx", ".docx"], None => all

    #### Return [rustedpy]
     - Ok: files as list
     - Err: errortext as str
    """

    dirpath = Path(dirpath)
    if not dirpath.exists():
        err = f"DirNotFoundError: '{dirpath}'"
        Trace.debug(err)
        return Err(err)

    ret = []
    files = os.listdir(dirpath)
    for file in files:
        if (dirpath / file).is_file():
            if extensions is None or Path(dirpath, file).suffix in extensions:
                ret.append(file)

    return Ok(ret)
