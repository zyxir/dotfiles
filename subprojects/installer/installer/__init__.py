"""Cross-platform installation script for my dotfiles."""

import argparse
import sys
import time

from installer.ahk import ahk_install_all
from installer.cmd import run
from installer.file import link
from installer.font import install_zyfonts
from installer.man import man_cmd
from installer.opt import Options
from installer.os import IS_LINUX, IS_WINDOWS, IS_WSL
from installer.path import setup_directory, to_path
from installer.rime import win_rime_setup
from installer.style import emph, setup_logging


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
    parser.add_argument("--debug", action="store_true", help="show debug messages")
    args = parser.parse_args()
    opt = Options(
        dry=args.dry,
        switch=args.switch or args.complete,
        fonts=args.fonts or args.complete,
    )

    # Set up logging.
    setup_logging(args.debug)

    # Make sure the script is run in the correct directory.
    try:
        setup_directory()
    except Exception:
        print("Cannot locate the dotfiles repo.")
        sys.exit(1)

    # Notify a dry run.
    if opt.dry:
        print("This is a {}. Nothing is actually installed.".format(emph("dry run")))

    # Start timing.
    start_time = time.time()

    # Install dot files.
    if IS_LINUX:
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
    elif IS_WINDOWS:
        link("./apps/git/dot_gitconfig", "~/.gitconfig", opt)
        link(
            "./shell/PowerShell/Microsoft.PowerShell_profile.ps1",
            "~/Documents/WindowsPowerShell/Microsoft.PowerShell_profile.ps1",
            opt,
        )
        link("./apps/rime", "%appdata%/rime", opt)
        win_rime_setup(opt)
        ahk_install_all("./AutoHotkey", opt)

    # Install fonts.
    if opt.fonts:
        install_zyfonts(opt)

    # Suggest manual commands.
    if IS_WSL:
        man_cmd(
            "/usr/share/applications/emacs.desktop",
            "Run the following command to enable starting Emacs from Windows:",
            "sudo cp {} /usr/share/applications/emacs.desktop".format(
                to_path("./apps/emacs/emacs.desktop")
            ),
        )

    # Say goodbye.
    elapsed_time = time.time() - start_time
    print(f"Finished in {elapsed_time:.3f} seconds.")
