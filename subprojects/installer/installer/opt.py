"""Installer options."""

from dataclasses import dataclass


@dataclass
class Options:
    """Class for storing installer options."""

    # Whether to perform a dry run.
    dry: bool = False
    # Whether to do a home-manager switch.
    switch: bool = False
    # Whether to install fonts.
    fonts: bool = False
