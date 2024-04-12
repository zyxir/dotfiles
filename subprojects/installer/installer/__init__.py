"""Cross-platform installation script for my dotfiles."""

import sys
import argparse
import platform
from installer.ahk import ahk_install_all
from installer.cmd import run

from installer.file import copy, link
from installer.opt import Options
from installer.path import setup_directory
from installer.rime import win_rime_setup
from installer.style import emph, setup_logging

# OS constants.
WINDOWS = platform.system() == "Windows"
LINUX = platform.system() == "Linux"
WSL = "WSL" in platform.uname().release


def main():
    # Get options through arguments.
    parser = argparse.ArgumentParser(description="Install Zyxir's dotfiles.")
    parser.add_argument(
        "--dry",
        action="store_true",
        help="perform a dry run (only print; don't install anything)",
    )
    parser.add_argument(
        "--fonts",
        action="store_true",
        help="install fonts from possible archives",
    )
    parser.add_argument(
        "--switch",
        action="store_true",
        help="do a home-manager switch",
    )
    parser.add_argument(
        "--complete",
        action="store_true",
        help="perform a complete run: do every optional actions",
    )
    args = parser.parse_args()
    opt = Options(
        dry=args.dry or args.complete,
        switch=args.switch or args.complete,
        fonts=args.fonts or args.complete,
    )

    # Set up logging.
    setup_logging()

    # Make sure the script is run in the correct directory.
    try:
        setup_directory()
    except Exception:
        print("Cannot locate the dotfiles repo.")
        sys.exit(1)

    # Notify a dry run.
    if opt.dry:
        print("This is a {}. Nothing is actually installed.".format(emph("dry run")))

    # Install dot files.
    if WINDOWS:
        link("./apps/git/dot_gitconfig", "~/.gitconfig", opt)
        link(
            "./shell/PowerShell/Microsoft.PowerShell_profile.ps1",
            "~/Documents/WindowsPowerShell/Microsoft.PowerShell_profile.ps1",
            opt,
        )
        copy("./apps/rime", "%appdata%/rime", opt)
        win_rime_setup(opt)
        ahk_install_all("./AutoHotkey", opt)
    if LINUX:
        link("./shell/bash/bashrc", "~/.bashrc", opt)
        link("./shell/bash/bash_profile", "~/.bash_profile", opt)
        link("./shell/zsh/zshrc", "~/.zshrc", opt)
        link("./shell/zsh/zshenv", "~/.zshenv", opt)
        link("./apps/fontconfig/fonts.conf", "~/.config/fontconfig/fonts.conf", opt)
        link(
            "./apps/nix/home-manager/home.nix",
            "~/.config/home-manager/home.nix",
            opt,
        )
        if opt.switch:
            run("home-manager switch", opt)

    # # Additional steps for a complete run.
    # if fonts:
    #     install_fonts(dry)
