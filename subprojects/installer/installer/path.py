"""Utility for path management."""

import os
from pathlib import Path


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
            os.chdir(Path.cwd().parent)
