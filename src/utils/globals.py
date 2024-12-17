"""
    (c) Jürgen Schoenemeyer, 17.12.2024

    PUBLIC:
     - DRIVE
     - BASE_PATH
     - SYSTEM_ENV_PATHS
"""

import os
import sys
from pathlib import Path

DRIVE = Path(__file__).drive
BASE_PATH = Path(sys.argv[0]).parent

system_paths = os.getenv("PATH")
if system_paths[-1:] == ";":
    system_paths = system_paths[:-1]

SYSTEM_ENV_PATHS = system_paths.split(";")
