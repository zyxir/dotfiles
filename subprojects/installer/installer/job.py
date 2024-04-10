"""Definition of jobs.

A job defines an atomic operation of dotfiles installtion.
"""

import logging
from typing import Any, Callable

from installer.style import print_done, print_failed


class Job:
    """An atomic operation of dotfiles installation.

    `msg` is printed when the job begins, and `action` is a function that
    describes what the job actually does.
    """

    def __init__(self, msg: str, action: Callable[[], Any]) -> None:
        print(msg, end="")
        try:
            action()
        except Exception as e:
            print_failed()
            logging.error(e)
        else:
            print_done()
