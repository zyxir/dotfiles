"""Utility for styled printing."""

import logging
from os import PathLike
from typing import Union


def emph(s: str) -> str:
    """Emphasize `s` by making it cyan and bold."""
    return "\u001b[36;1m" + s + "\u001b[0m"

def emph_path(path: Union[str, PathLike]) -> str:
    """Emphasize `path` by making it cyan."""
    return "\u001b[36m" + str(path) + "\u001b[0m"

def emph_cmd(cmd: str) -> str:
    """Emphasize `cmd` by making it magenta."""
    return "\u001b[35m" + cmd + "\u001b[0m"

def print_done():
    """Print a \"done\"."""
    print("done")

def print_failed():
    """Print a \"failed\"."""
    print("\u001b[31m" + "failed" + "\u001b[0m")

class Formatter(logging.Formatter):

    # Log indicators.
    INDICATORS = {
        # No color for debugs.
        logging.DEBUG: "D",
        # Green for infos.
        logging.INFO: "\u001b[32m" + "I" + "\u001b[0m",
        # Bold yellow for warnings.
        logging.WARNING: "\u001b[33;1m" + "W" + "\u001b[0m",
        # Bold red for errors.
        logging.ERROR: "\u001b[31;1m" + "E" + "\u001b[0m",
        # Bold red for criticals.
        logging.CRITICAL: "\u001b[31;1m" + "CRIT" + "\u001b[0m",
    }

    def format(self, record: logging.LogRecord) -> str:
        prefix = "[" + self.INDICATORS[record.levelno] + "] "
        content = str(record.msg)
        return prefix + content

def setup_logging(debug: bool = False):
    """Set up logging."""
    sh = logging.StreamHandler()
    sh.setFormatter(Formatter())
    logging.getLogger().addHandler(sh)
    if debug:
        logging.getLogger().setLevel(logging.DEBUG)
