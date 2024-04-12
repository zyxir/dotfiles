#!/usr/bin/python
"""This script build the installer package into a single .pyz file, put it at
the root of the dotfiles repository, and remove all temporary files.
"""

import shutil
import subprocess
import sys
from pathlib import Path

# The directory of this script.
curdir = Path(__file__).parent

# Compile to a single file.
if not shutil.which("shiv"):
    print("'shiv' is not available.")
    sys.exit(1)
else:
    cmd = "shiv -c installer -o ../../install.pyz ."
    subprocess.run(cmd.split(), cwd=curdir)

# Remove temporary files.
temp_files = [
    curdir.joinpath("build"),
    curdir.joinpath("installer.egg-info")
]
for file in temp_files:
    if file.exists():
        if file.is_dir():
            shutil.rmtree(file)
        else:
            file.unlink()
