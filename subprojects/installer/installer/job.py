"""Definition of jobs.

A job defines an atomic operation of dotfiles installtion.
"""

from dataclasses import dataclass
import logging
from typing import Callable

from installer.style import print_done, print_failed


@dataclass
class Job:
    """An atomic operation of dotfiles installation.

    `msg` is printed when the job begins, and `action` is a function that
    describes what the job actually does (defaults to the `do` method).
    """
    # The message to show.
    msg: str
    # The action to do.
    action: Callable[[], None]

    def run(self) -> None:
        # No newline printed, we have to manually flush.
        print(self.msg, end="...", flush=True)
        try:
            self.action()
        except Exception as e:
            print_failed()
            logging.error(e)
        else:
            print_done()
