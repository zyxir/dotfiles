"""Utility about manual operations."""


from logging import warning
from typing import Union
from typing import Callable

from installer.path import to_path
from installer.style import emph_cmd


def man_cmd(pred: Union[Callable[[], bool], str], instr: str, cmd: str) -> None:
    """Print `instr` to run `cmd` when `pred` is not satisfied.

    If `pred` is a callable, it should return a boolean, otherwise it should be
    a path which is checked for existence.
    """
    pred_result = False
    if isinstance(pred, str):
        pred_result = to_path(pred).exists()
    else:
        try:
            pred_result = pred()
        except Exception as e:
            warning(e)
            pass
    if not pred_result:
        print(instr)
        print("  " + emph_cmd(cmd))
