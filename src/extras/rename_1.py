# python rename.py

import os
import shutil
from pathlib import Path

from utils.globals import BASE_PATH
from utils.trace   import Trace

base_path = BASE_PATH / "../data"

replace = ["-fast#", "-faster#"]

def main() -> None:

    def check_dirs( path: Path ):
        for mypath in path.iterdir():
            if mypath.is_dir():
                if replace[0] in str(mypath):
                    newpath = str(mypath).replace( replace[0], replace[1] )
                    shutil.move(mypath, newpath)
                    Trace.info(f"rename {mypath} to {newpath}")
                else:
                    check_dirs( mypath )

    def check_files( path: Path ):
        for mypath in path.iterdir():
            if mypath.is_file():
                if replace[0] in str(mypath):
                    new_filename =  str(mypath).replace( replace[0], replace[1] )
                    os.rename( mypath, new_filename)
                    Trace.info(f"rename {mypath} to {new_filename}")
            else:
                check_files( mypath )

    # check_dirs( Path(base_path) )
    # check_files( Path(base_path) )

if __name__ == "__main__":
    main()
