#!/usr/bin/python3
"""This file calls the `installer` module to install the dotfiles."""

from importlib.machinery import SourceFileLoader
from pathlib import Path

installer_path = Path(__file__).parent.joinpath("subprojects/installer/installer/__main__.py")
installer = SourceFileLoader("installer", str(installer_path)).load_module()

if (
    __name__ == "__main__"
    and hasattr(installer, "__main__")
    and hasattr(installer.__main__, "__call__")
):
    installer.__main__()
