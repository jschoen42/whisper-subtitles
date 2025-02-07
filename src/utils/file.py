"""
    © Jürgen Schoenemeyer, 29.01.2025

    src/utils/file.py

    PUBLIC:
     # timestamp
     - get_modification_timestamp(filename: Path | str) -> float
     - set_modification_timestamp(filename: Path | str, timestamp: float) -> None

     # check
     - check_path_exists(path: str) -> bool
     - check_file_exists(filepath: Path | str, filename: str) -> bool

     # Listing
     - listdir(path: Path | str ) -> Tuple[List[str], List[str]]
     - listdir_match_extention(path: Path | str, extensions: List[str] | None = None) -> Tuple[List[str], List[str]]

     # folder operations
     - list_folders(path: Path | str) -> List[str]:
     - clear_folder(path: Path | str) -> None:
     - delete_folder_tree(dest_path: Path | str, relax: bool = False) -> bool:
     - create_folder( folderpath: Path | str ) -> bool:
     - make_dir(path: Path | str) -> None:
     - delete_file(path: Path | str, filename: str) -> None:
     - beautify_path( path: Path | str ) -> str:

     #
     - get_trace_path(filepath: Path | str) -> str:
     - get_files_in_folder( path: Path ) -> List[str]
     - get_folders_in_folder( path: Path ) -> List[str]
     - get_save_filename( path: Path, stem: str, suffix: str ) -> str

     - import_text( folderpath: Path | str, filename: Path | str, encoding: str="utf-8", show_error: bool=True ) -> str | None
     - import_json( folderpath: Path | str, filename: str, show_error: bool=True ) -> Any
     - import_json_timestamp( folderpath: Path | str, filename: str, show_error: bool=True ) -> Tuple[Any, float | None]

     - export_text( folderpath: Path | str, filename: str, text: str, encoding: str="utf-8", timestamp: None | float=0, ret_lf: bool=False, create_new_folder: bool=True, show_message: bool=True ) -> str | None
     - export_json( folderpath: Path | str, filename: str, data: Dict[str, Any] | List[Any], timestamp: float | None = None, show_message: bool=True ) -> str | None
     - export_binary_file(filepath: Path | str, filename: str, data: bytes, _timestamp: float=0, create_new_folder: bool=False) -> None
     - export_file(filepath: Path|str, filename: str, text: str, in_type: str | None = None, timestamp: float=0, create_new_folder: bool=True, encoding: str ="utf-8", overwrite: bool=True) -> None | str
    #
     - get_filename_unique(dirpath: Path, filename: str) -> str
     - find_matching_file(path_name: str) -> bool | str
     - find_matching_file_path(dirname: Path, filename: str) -> Path | bool
     - get_valid_filename(name: str) -> str
     - get_file_infos(path: Path | str, filename: str, _in_type: str) -> None | Dict
    #
     - copy_my_file(source: str, dest: str, _show_updated: bool) -> bool

    PRIVATE:
     - _increment_filename(filename_stem: str) -> str
"""

import shutil
import os
import re
import glob
import json
import hashlib
import datetime
import filecmp

from typing import Any, Dict, List, Tuple
from os.path import isfile, isdir, join
from pathlib import Path

from utils.trace import Trace

# timestamp

def get_modification_timestamp(filename: Path | str) -> float:
    try:
        ret = os.path.getmtime(Path(filename))
    except OSError as err:
        Trace.error(f"{err}")
        return 0

    return ret

def set_modification_timestamp(filename: Path | str, timestamp: float) -> None:
    try:
        os.utime(Path(filename), (timestamp, timestamp)) # atime and mtime
    except OSError as err:
        Trace.error(f"set_modification_timestamp: {err}")

# check

def check_path_exists(path: Path | str) -> bool:
    return os.path.exists(path)

def check_file_exists(filepath_start: Path | str, filepath_end: Path | str) -> bool:

    # case sensitive

    # "/dir1/dir2/dir3" + "/file.ext"
    # "/dir1/dir2" + "/dir3/file.ext"
    # "/dir1" + "/dir2/dir3/file.ext"
    # "" + "/dir1/dir2/dir3/file.ext"

    full_path = Path(filepath_start) / filepath_end

    filepath = full_path.parent
    filename = full_path.name

    if not filepath.exists():
        Trace.error(f"directory missing '{filepath}'")
        return False

    try:
        filenames = os.listdir(filepath)
    except OSError as err:
        Trace.error(f"{err}")
        return False

    if filename in filenames:
        return True
    else:
        Trace.error(f"file missing {full_path}")
        return False

# folder Listing

def listdir(path: Path | str ) -> Tuple[List[str], List[str]]:
    return listdir_match_extention( path, [".*"] )

#  extensions: [".zip", ".story", ".xlsx", ".docx"], ".*" => all

def listdir_match_extention(path: Path | str, extensions: List[str]) -> Tuple[List[str], List[str]]:
    path = Path(path)

    extensions = list({ext.lstrip(".") for ext in extensions})

    files:   List[str] = []
    folders: List[str] = []

    if not check_path_exists(path):
        Trace.error( f"folder not found '{path.as_posix()}'" )
        return files, folders

    for file in os.listdir(path):
        if file.startswith("~"):
            Trace.warning(f"skip temp file '{file}'")
            continue

        if os.path.isfile(path / file):
            for extention in extensions:
                if extention == "*" or file.endswith("." + extention):
                    files.append(file)
                    break

        elif os.path.isdir(path / file):
            folders.append(file)

        else:
            Trace.warning(f"skip unknown filetype '{file}'")

    return files, folders

def list_folders(path: Path | str) -> List[str]:
    path = Path(path)

    folders: List[str] = []
    try:
        for file in os.listdir(path):
            if os.path.isdir(os.path.join(path, file)):
                folders.append(file)
    except OSError as err:
        Trace.error(f"{err}")

    return folders

def clear_folder(path: Path | str) -> None:
    path = Path(path)

    for filename in os.listdir(path):
        filepath = os.path.join(path, filename)

        try:
            shutil.rmtree(filepath)
        except OSError as err:
            error = str(err).split(":")[0]
            try:
                os.remove(filepath)
            except OSError:
                Trace.fatal( f"shutil.rmtree {error} '{get_trace_path(filepath)}'")

def delete_folder_tree(dest_path: Path | str, relax: bool = False) -> bool:
    dest_path = Path(dest_path)

    ret = False
    if os.path.exists(dest_path):
        try:
            shutil.rmtree(dest_path)
            ret = True
        except OSError as msg:
            if relax and len(os.listdir(dest_path)) == 0:
                Trace.warning( f"relaxed mode: {msg}")
            else:
                Trace.fatal( f"shutil.rmtree: {msg}")
    else:
        ret = True

    return ret

def create_folder( folderpath: Path | str ) -> bool:
    folderpath = Path( folderpath )

    if not folderpath.is_dir():
        try:
            os.makedirs(folderpath)
            Trace.update( f"makedir: {folderpath}")
            return True
        except OSError as error:
            error_msg = str(error).split(":")[0]
            Trace.error( f"{error_msg}: {folderpath}")
            return False
    else:
        return False

def make_dir(path: Path | str) -> None:
    path = Path(path)

    path.mkdir(parents=True, exist_ok=True)

def delete_file(path: Path | str, filename: str) -> None:
    filepath = Path(path) / filename

    if filepath.is_file():
        try:
            filepath.unlink()
            Trace.update(f"file '{filepath}' deleted")
        except OSError as err:
            Trace.error(f"{err}")

def beautify_path( path: Path | str ) -> str:
    return str( path ).replace("\\\\", "/")

#
# D:\Projekte_P4\Articulate-Storyline\WebService1\_workdir\jobs\c4c3dda9-0e58-49dd-86d0-151fe2267edb\tmp\media\image\resultslideVectorText.png -> media\image\resultslideVectorText.png
#
def get_trace_path(filepath: Path | str) -> str:

    tmp_path = os.path.normpath(filepath).replace("\\", "/")

    if "/_workdir/" in tmp_path:
        trace_path = "./" + tmp_path.split("/tmp/")[1]
    else:
        trace_path = tmp_path

    # Trace.info(f"trace_path: {trace_path}")
    return trace_path


def get_files_in_folder( path: Path ) -> List[str]:
    return [f for f in os.listdir(path) if isfile(join(path, f))]

def get_folders_in_folder( path: Path ) -> List[str]:
    return [f for f in os.listdir(path) if isdir(join(path, f))]

def get_save_filename( path: Path, stem: str, suffix: str ) -> str:
    files = get_files_in_folder( path )

    name = stem
    while name + suffix in files:
        name = _increment_filename( name )

    return name + suffix

def import_text( folderpath: Path | str, filename: Path | str, encoding: str="utf-8", show_error: bool=True ) -> str | None:
    filepath = Path(folderpath, filename)

    if filepath.is_file():
        try:
            with open(filepath, encoding=encoding) as file:
                data = file.read()
            return data

        except OSError as error:
            Trace.error(f"{error}")
            return None

        except UnicodeDecodeError as error:
            Trace.error(f"{filepath}: {error}")
            return None

    else:
        if show_error:
            Trace.error(f"file not exist {filepath.resolve()}")
        return None

def import_json( folderpath: Path | str, filename: str, show_error: bool=True ) -> Any | None:
    result = import_text(folderpath, filename, show_error=show_error)
    if result:
        data = json.loads(result)
        return data
    else:
        return None

def import_json_timestamp( folderpath: Path | str, filename: str, show_error: bool=True ) -> Tuple[Any | None, float]:
    ret = import_json(folderpath, filename, show_error=show_error)
    if ret:
        return ret, get_modification_timestamp(Path(folderpath, filename))
    else:
        return None, 0.0

def export_text( folderpath: Path | str, filename: str, text: str, encoding: str="utf-8", timestamp: None | float=0, ret_lf: bool=False, create_new_folder: bool=True, show_message: bool=True) -> str | None:
    folderpath = Path(folderpath)
    filepath   = Path(folderpath, filename)

    if ret_lf:
        text = text.replace("\n", "\r\n")

    exist = False
    try:
        with open(filepath, "r", encoding=encoding) as file:
            text_old = file.read()
            exist = True
    except OSError:
        text_old = ""

    if exist:
        if text == text_old:
            if show_message:
                Trace.info(f"not changed '{filepath}'")
            return str(filename)

    if create_new_folder:
        create_folder(folderpath)

    try:
        with open(filepath, "w", encoding=encoding) as file:
            file.write(text)

        if timestamp and timestamp != 0:
            set_modification_timestamp(filepath, timestamp)

        if show_message:
            if text_old == "":
                Trace.update(f"created '{filepath}'")
            else:
                Trace.update(f"changed '{filepath}'")

        return str(filename)

    except OSError as error:
        error_msg = str(error).split(":")[0]
        Trace.error(f"{error_msg} - {filepath}")
        return None

def export_json(folderpath: Path | str, filename: str, data: Dict[str, Any] | List[Any], timestamp: float | None = None, show_message: bool=True) -> str | None:
    text = json.dumps(data, ensure_ascii=False, indent=2)

    return export_text(folderpath, filename, text, encoding = "utf-8", timestamp = timestamp, show_message = show_message)

def export_binary_file(filepath: Path | str, filename: str, data: bytes, _timestamp: float=0, create_new_folder: bool=False) -> None:
    if create_new_folder:
        if not os.path.isdir(filepath):
            os.makedirs(filepath)
            Trace.update( f"makedir '{filepath}'")

    with open(Path(filepath, filename), "wb") as binary_file:
        binary_file.write(data)

def export_file(
    filepath: Path | str,
    filename: str,
    text: str,
    in_type: str | None = None,
    timestamp: float=0.0,
    create_new_folder: bool=True,
    encoding: str ="utf-8",
    overwrite: bool=True
) -> None | str:
    trace_export_path_folder = get_trace_path(Path(filepath))
    trace_export_path        = get_trace_path(Path(filepath, filename))

    if text == "":
        Trace.error(f"text empty '{trace_export_path}'")
        return None

    if overwrite:
        my_filename = filename
    else:
        tmp = filename.split(".")
        ext = tmp.pop()
        dest2 = ".".join(tmp)
        copy = ""

        c = 0
        while Path(filepath, (dest2 + copy + "." + ext)).is_file():
            if c == 0:
                c = 2
            else:
                c += 1
            copy = "_[" + str(c) + "]"

        my_filename = dest2 + copy + "." + ext

    try:
        with open(Path(filepath, my_filename), "r", encoding=encoding) as file:
            ref_text = file.read()
    except OSError:
        ref_text = ""

    if text == ref_text:
        # Trace.wait( f"{my_filename}")

        if in_type:
            Trace.info( f"'{in_type}' not changed '{trace_export_path}'")
        else:
            Trace.info( f"not changed '{trace_export_path}'")

        return my_filename

    else:
        if create_new_folder:
            if not os.path.isdir(filepath):
                try:
                    os.makedirs(filepath)
                    Trace.update( f"makedir: '{trace_export_path_folder}'")
                except OSError as err:
                    error = str(err).split(":")[0]
                    Trace.error(f"{error}: '{trace_export_path_folder}'")
                    return None

        try:
            with open(Path(filepath, my_filename), "w", encoding=encoding) as file:
                file.write(text)

            if timestamp != 0:
                set_modification_timestamp(Path(filepath, my_filename), timestamp)

            if ref_text == "":
                if in_type:
                    Trace.update( f"'{in_type}' created '{trace_export_path}'")
                else:
                    Trace.update( f"created '{trace_export_path}'")
            else:
                if in_type:
                    Trace.update( f"'{in_type}' changed '{trace_export_path}'")
                else:
                    Trace.update( f"changed '{trace_export_path}'")

            return my_filename

        except OSError as err:
            error = str(err).split(":")[0]
            Trace.error(f"{error} '{trace_export_path}'")
            return None

# increment_filename(filename_stem: str) -> str:
#
# 'filaname'     -> 'filaname (1)'
# 'filaname (1)' -> 'filaname (2)'
# 'filaname (2)' -> 'filaname (3)'
# ...

def _increment_filename(filename_stem: str) -> str:
    pattern = r"^(.*?)(?: \((\d+)\))?$"

    match = re.match(pattern, filename_stem)
    if match:
        base_name, number = match.groups()
        number = int(number) + 1 if number else 1

        new_name = f"{base_name} ({number})"
        return new_name

    return filename_stem

def get_filename_unique(dirpath: Path, filename: str) -> str:
    suffix = Path(filename).suffix
    stem = Path(filename).stem

    number = 1
    append = ""
    while os.path.isfile(dirpath / (stem + append + suffix)):
        number += 1
        append = "_[" + str(number) + "]"

    return stem + append + suffix

def find_matching_file(path_name: str) -> bool | str:
    s = glob.glob(path_name)

    if len(s) == 0:
        Trace.error(f"file not found: {path_name}")
        return False

    if len(s) > 1:
        Trace.error(f"file not unique: {path_name} - {s}")
        return False

    return s[0].replace("\\", "/")

def find_matching_file_path(dirpath: Path, filename: str) -> None | Path:
    filepath = str(dirpath / filename)

    s = glob.glob( filepath )

    if len(s) == 0:
        Trace.error(f"file not found: {filepath}")
        return None

    if len(s) > 1:
        Trace.error(f"file not unique: {filepath} - {s}")
        return None

    return Path(s[0].replace("\\", "/"))

def get_valid_filename(name: str) -> str:
    s = str(name).strip().replace(" ", "_")
    s = re.sub(r"(?u)[^-\w.]", "", s)
    #if s in {"", ".", ".."}:
    #    raise SuspiciousFileOperation("Could not derive file name from '%s'" % name)
    return s

def get_file_infos(path: Path | str, filename: str, _in_type: str) -> None | Dict[str, Any]:
    filepath = Path(path, filename)

    if os.path.isfile(filepath):
        with open(filepath, "rb") as file:
            md5 = hashlib.md5(file.read()).hexdigest()

        size           = os.path.getsize(filepath)
        timestamp      = get_modification_timestamp(filepath)
        date_timestamp = datetime.datetime.fromtimestamp(timestamp).astimezone().isoformat()

        if timestamp.is_integer():
            data_dot_net = date_timestamp
        else:
            decimal_digits = f"{timestamp:.7f}".split(".")[1]
            data_dot_net = date_timestamp[:20] + decimal_digits + date_timestamp[-6:]

        return {
            "date":       date_timestamp, # 2024-08-13T09:38:38.935807+02:00  (6 decimal digits)
            "dateDotNet": data_dot_net,   # 2024-08-13T09:38:38.9358065+02:00 (7 decimal digits)
            "bytes":      size,
            "md5":        md5
        }
    else:
        Trace.error( f"not found: {filepath}" )
        return None

def copy_my_file(source: str, dest: str, _show_updated: bool) -> bool:
    new_timestamp = get_modification_timestamp(source)

    if not os.path.exists(dest) or not filecmp.cmp(source, dest):
        try:
            shutil.copyfile(source, dest)
            set_modification_timestamp(dest, new_timestamp)
            Trace.info( f"copy {dest}" )

        except OSError as err:
            Trace.error(f"{err}")
            return False

    return True

