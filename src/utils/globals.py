"""
    © Jürgen Schoenemeyer, 20.12.2024

    PUBLIC:
     - DRIVE: Path
     - BASE_PATH: Path
     - SYSTEM_ENV_PATHS: list
"""

import os
import sys
from pathlib import Path

DRIVE: Path     = Path(Path(__file__).drive)
BASE_PATH: Path = Path(sys.argv[0]).parent.parent

system_paths = os.getenv("PATH")
if system_paths[-1:] == ";":
    system_paths = system_paths[:-1]

SYSTEM_ENV_PATHS: list = system_paths.split(";")
