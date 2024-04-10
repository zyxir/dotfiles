"""Utility for styled printing."""

from pathlib import Path
from typing import Union


def emph_path(path: Union[str, Path]) -> str:
    """Emphasize `path` by making it cyan."""
    return "\u001b[36m" + str(path) + "\u001b[0m"

def print_done():
    """Print a \"done\"."""
    print("done")

def print_failed():
    """Print a \"failed\"."""
    print("\u001b[31m" + "failed" + "\u001b[0m")
