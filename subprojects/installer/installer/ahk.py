"""Utility for handling AutoHotkey scripts."""


import logging
from pathlib import Path

from installer.cmd import run_cmd
from installer.file import copy_path
from installer.job import Job
from installer.opt import Options
from installer.path import to_path
from installer.style import emph_path


def ahk_install_all(dir: str, opt: Options) -> None:
    """Install all AutHotkey scripts in `dir`, handling errors."""
    dir_path = to_path(dir)
    if dir_path.exists():
        for file in dir_path.glob("*.ahk"):
            ahk_install(file, opt)
    else:
        logging.warn(f"{emph_path(dir)} not found, no AutoHotkey script is installed.")


def ahk_install(file: Path, opt: Options) -> None:
    """Install AutoHotkey script `file`, handling errors."""
    msg = f"Installing AutoHotkey script {emph_path(file)}."

    def action() -> None:
        ahk2exe = ensure_ahk2exe()
        exe = ahk_compile_file(file, ahk2exe, opt)
        ahk_install_exe(exe, opt)

    Job(msg, action).run()


def ensure_ahk2exe() -> Path:
    """Ensure and return the \"Ahk2Exe.exe\" program."""
    path = to_path("C:\\Program Files\\AutoHotkey\\Compiler\\Ahk2Exe.exe")
    if not path.exists():
        raise Exception("Ahk2Exe.exe not found")
    return path


def ahk_compile_file(file: Path, ahk2exe: Path, opt: Options) -> Path:
    """Compile \".ahk\" `file` into a \".exe\" program.

    Return the path of the \".exe\" program.
    """
    cmd = f"{ahk2exe} /in {file}"
    if run_cmd(cmd, opt, cwd=file.parent) == 0:
        return file.parent.joinpath(file.stem + ".exe")
    else:
        raise Exception(f"Error compiling {emph_path(file)}")


def ahk_install_exe(file: Path, opt: Options):
    """Install AutoHotkey program \"file\" into the proper path."""
    startup_path = to_path("%appdata%/Microsoft/Windows/Start Menu/Programs/Startup")
    dst_path = startup_path.joinpath(file.name)
    copy_path(file, dst_path, opt)
