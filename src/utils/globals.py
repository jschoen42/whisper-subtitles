"""
    © Jürgen Schoenemeyer, 10.01.2025

    PUBLIC:
     - DRIVE: Path
     - BASE_PATH: Path
     - SYSTEM_ENV_PATHS: List
"""

import os
import sys

from typing import List
from pathlib import Path

DRIVE: Path     = Path(Path(__file__).drive)
BASE_PATH: Path = Path(sys.argv[0]).parent.parent

system_paths = os.getenv("PATH")
if system_paths is None:
    system_paths = ""

if system_paths[-1:] == ";":
    system_paths = system_paths[:-1]

SYSTEM_ENV_PATHS: List[str] = system_paths.split(";")
