"""
    © Jürgen Schoenemeyer, 20.12.2024

    PUBLIC:
     - get_modification_timestamp(filename: Path | str) -> float
     - set_modification_timestamp(filename: Path | str, timestamp: float) -> None
    #
     - check_path_exists(path: str) -> bool
     - check_file_exists(filepath: str, filename: str) -> bool
     - check_excel_file_exists(filename: str) -> bool
    #
     - list_files(path: str, extensions: list) -> list
     - list_directories(path: str) -> list
     - listdir_match_extention(folder_path: Path | str, extensions: list=None) -> list
    #
     - clear_folder(path: str) -> None
     - delete_folder_tree(dest_path: str, relax: bool = False) -> bool
     - create_folder( folderpath: Path | str ) -> bool
     - make_dir(in_path)
     - beautify_path( path: Path | str ) -> str
    #
     - get_trace_path(filepath: Path | str) -> str
     - get_files_in_folder( path: Path ) -> list
     - get_folders_in_folder( path: Path ) -> list
     - get_save_filename( path, stem, suffix ) -> str
     - export_binary_file(filepath: Path | str, filename: str, data: bytes, _timestamp: int=0, create_folder: bool=False) -> None
     - export_file(filepath: Path|str, filename: str, text: str, in_type: str = None, timestamp: int=0, create_folder: bool=False, encoding: str ="utf-8", overwrite: bool=True) -> str
    #
     - get_filename_unique(dirpath: Path, filename: str) -> str
     - find_matching_file(path_name: str) -> bool | str
     - find_matching_file_path(dirname: Path, filename: str) -> Path | bool
     - get_valid_filename(name: str) -> str
     - get_file_infos(path: Path | str, filename: str, _in_type: str) -> None | dict
    #
     - copy_my_file(source: str, dest: str, _show_updated: bool) -> bool
    #
     - convert_datetime( time_string: str ) -> int
"""

import shutil
import os
import re
import codecs
import glob
import hashlib
import datetime
import filecmp

from os.path import isfile, isdir, join
from pathlib import Path

try:
    from dateutil.parser import parse
except ImportError:
    pass

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

def check_path_exists(path: str) -> bool:
    return os.path.exists(path)

def check_file_exists(filepath: str, filename: str) -> bool: # case sensitive
    path = Path(filepath, filename )

    filepath = path.parent
    filename = path.name

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
        Trace.error(f"file missing {path}")
        return False

def check_excel_file_exists(filename: str) -> bool:
    if str(filename)[-5:] != ".xlsx":
        return False

    return os.path.isfile(filename)

# dir listing

def list_files(path: str, extensions: list) -> tuple[list, list]:
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

    return files, dirs

def list_directories(path: str) -> list:
    ret: list = []

    try:
        for file in os.listdir(path):
            if os.path.isdir(os.path.join(path, file)):
                ret.append(file)
    except OSError as err:
        Trace.error(f"{err}")

    return ret

def listdir_match_extention(folder_path: Path | str, extensions: list=None) -> list:

    #  extensions: [".zip", ".story", ".xlsx", ".docx"], None => all

    ret = []
    files = os.listdir(Path(folder_path))
    for file in files:
        if Path(folder_path, file).is_file():
            if extensions is None or Path(folder_path, file).suffix in extensions:
                ret.append(file)

    return ret

def clear_folder(path: str) -> None:
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

def delete_folder_tree(dest_path: str, relax: bool = False) -> bool:
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

def make_dir(in_path):
    path = Path(in_path)
    path.mkdir(parents=True, exist_ok=True)

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

def get_files_in_folder( path: Path ) -> list:
    return [f for f in os.listdir(path) if isfile(join(path, f))]

def get_folders_in_folder( path: Path ) -> list:
    return [f for f in os.listdir(path) if isdir(join(path, f))]

def get_save_filename( path: Path, stem: str, suffix: str ) -> str:
    files = get_files_in_folder( path )

    name = stem
    while name + suffix in files:
        name = _increment_filename( name )

    return name + suffix

def export_binary_file(filepath: Path | str, filename: str, data: bytes, _timestamp: float=0, create_new_folder: bool=False) -> None:
    if create_new_folder:
        if not os.path.isdir(filepath):
            os.makedirs(filepath)
            Trace.update( f"makedir '{filepath}'")

    with open(Path(filepath, filename), "wb") as binary_file:
        binary_file.write(data)


def export_file(filepath: Path|str, filename: str, text: str, in_type: str = None, timestamp: float=0, create_new_folder: bool=True, encoding: str ="utf-8", overwrite: bool=True) -> str:
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
        with codecs.open(Path(filepath, my_filename), "r", encoding) as file: ###### ????
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

        try:
            with codecs.open(Path(filepath, my_filename), "w", encoding) as file:
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

"""
def get_filename_unique(path: str) -> str:
    tmp = path.split(".")
    ext = tmp.pop()
    dest2 = ".".join(tmp)
    copy = ""

    c = 0
    while os.path.isfile(dest2 + copy + "." + ext):
        if c == 0:
            c = 2
        else:
            c += 1
        copy = "_[" + str(c) + "]"

    dest = dest2 + copy + "." + ext
    return dest
"""

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
        Trace.error(f"file not unique: {path_name}")
        Trace.error(s)
        return False

    return s[0].replace("\\", "/")

def find_matching_file_path(dirpath: Path, filename: str) -> Path | bool:
    filepath = str(dirpath / filename)

    s = glob.glob( filepath )

    if len(s) == 0:
        Trace.error(f"file not found: {filepath}")
        return False

    if len(s) > 1:
        Trace.error(f"file not unique: {filepath}")
        Trace.error(s)
        return False

    return Path(s[0].replace("\\", "/"))

def get_valid_filename(name: str) -> str:
    s = str(name).strip().replace(" ", "_")
    s = re.sub(r"(?u)[^-\w.]", "", s)
    #if s in {"", ".", ".."}:
    #    raise SuspiciousFileOperation("Could not derive file name from '%s'" % name)
    return s

def get_file_infos(path: Path | str, filename: str, _in_type: str) -> None | dict:
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

def convert_datetime(time_string: str) -> int:
    my_time_string = parse(time_string.replace("UTC", ""))

    my_timestamp = int(datetime.datetime.timestamp(my_time_string))

    #print( "convert_datetime:", time_string, "->", my_time_string, " / ", my_time_string2, "=> epoch:", my_timestamp )
    return my_timestamp
