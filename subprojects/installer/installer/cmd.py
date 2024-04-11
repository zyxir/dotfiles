"""Utility for running external commands."""


import logging
from os import PathLike
import shutil
import subprocess
from typing import Optional
from installer.job import Job

from installer.opt import Options
from installer.style import emph_cmd, emph_path


def run(cmd: str, opt: Options, cwd: Optional[PathLike] = None, shell: bool = False) -> None:
    """Run external command `cmd`, handling errors."""
    msg = f"Running {emph_cmd(cmd)}"
    if cwd is not None:
        msg += f" in {emph_path(cwd)}"

    def action() -> None:
        ensure_exe(cmd)
        run_cmd(cmd, opt, cwd, shell)

    Job(msg, action).run()


def ensure_exe(cmd: str) -> None:
    """Ensure that the executable of `cmd` is available.

    If not available, raise an exception.
    """
    parts = cmd.split()
    if len(parts) == 0:
        raise Exception(f"No program specified in {emph_cmd(cmd)}")
    if shutil.which(parts[0]) is None:
        raise Exception(f"Executable {emph_cmd(parts[0])} is unavailable")


def run_cmd(
    cmd: str, opt: Options, cwd: Optional[PathLike] = None, shell: bool = False
) -> int:
    """Run external command `cmd`.

    Hide its `stdout`, redirect its `stderr` to `logging.warning`, and return
    its exit code.

    If `cwd` is not `None`, run the command in that path. If `shell` is `True`,
    run the command in a shell.
    """
    if opt.dry:
        return 0

    cmd_or_parts = cmd if shell else cmd.split()
    process = subprocess.Popen(
        cmd_or_parts,
        cwd=cwd,
        shell=shell,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if process.stderr:
        while process.poll() is not None:
            line = process.stderr.readline().strip()
            if line:
                logging.warning(line)
    return process.wait()
