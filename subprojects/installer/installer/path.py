"""Utility for path management."""

import os
from pathlib import Path
from typing import Optional, Tuple, Union

from installer.style import emph_path


def is_repo():
    """Return `True` if the current directory is the dotfiles repository."""
    readme = Path.cwd().joinpath("README.md")
    if not readme.exists():
        return False

    try:
        with open(readme, "r") as f:
            first_line = f.readline().strip()
            return first_line == "# Dotfiles"
    except Exception:
        return False


def setup_directory():
    """Change directory to the dotfiles repository.

    Identify the dotfiles repository with the first line of its README. Keep
    going up one level until the current directory is the dotfiles repository.
    """
    while not is_repo():
        cwd = Path.cwd()
        if cwd == cwd.parent:
            # If CWD equals its parent, it is the root.
            raise Exception("Cannot locate the repo till root")
        else:
            # Otherwise keep going up.
            os.chdir(cwd.parent)


def to_path(s: Union[str, os.PathLike]) -> Path:
    """Convert `s` to a normalized path.

    The resulted path is absolute, with all "~" expanded and all environment
    variables substituted.
    """
    s = os.path.expanduser(s)
    s = os.path.expandvars(s)
    path = Path(s).absolute()
    return path


def to_paths(s1: str, s2: str) -> Tuple[Path, Path]:
    """Covert `s1` and `s2` to paths via `to_path`."""
    return to_path(s1), to_path(s2)


def ensure_path(p: Union[str, os.PathLike]) -> Path:
    """Ensure that `p` exists, returning its path object."""
    path = to_path(p)
    if path.exists():
        return path
    else:
        raise Exception(f"{emph_path(p)} does not exist")


def some_path(*paths: str) -> Optional[Path]:
    """Return the first path available.

    The path is converted to a proper path object via `to_path`.
    """
    for p in paths:
        path = to_path(p)
        if path.exists():
            return path
    return None
