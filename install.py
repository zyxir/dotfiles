#!/bin/python3
"""Cross-platform installation script for my dotfiles."""

import os
import platform
import shutil
import subprocess
import sys
import typing as t
from pathlib import Path


def cyan(path: t.Union[str, Path]) -> str:
    """Wrap path in cyan ANSI escape codes."""
    return "\u001b[36m" + str(path) + "\u001b[0m"


class DirectoryError(Exception):
    """Raised when the script cannot be executed in the correct directory."""

    pass


def setup_directory():
    """Change directory to where this script is in.

    If __file__ is available, use the directory it is in.

    Otherwise, try to find a directory named "Unix" with a "install.py" inside,
    and change directory to it.  If no directory is found, raise an error.
    """
    if "__file__" in globals():
        os.chdir(Path(__file__).parent)
    else:
        candidates = list(Path.cwd().rglob("install.py"))
        if len(candidates) == 0:
            raise DirectoryError
        else:
            os.chdir(candidates[0].parent)


def copy(src: str, dst: str, dry: bool):
    """Copy src to dst, printing details.

    Work on a file or a directory.  Expand "~" to home directory.  Overwrite
    existing file(s).  Create directories if needed.

    :param src: The source.
    :param dst: The destination.
    :param dry: If True, perform a dry run.
    """
    # Convert to Path objects.
    src_path = Path(src).expanduser()
    dst_path = Path(dst).expanduser()

    # Raise error if src does not exist.
    if not src_path.exists():
        raise FileNotFoundError

    # Copy a single file.
    if src_path.is_file():
        if not dst_path.parent.exists():
            dst_path.parent.mkdir()
        print(f"Copying {cyan(src_path)} to {cyan(dst_path)}.")
        if not dry:
            shutil.copy(src_path, dst_path)
    # Copy a directory recursively.
    if src_path.is_dir():
        print(f"Copying {cyan(src_path)} to {cyan(dst_path)} recursively.")
        if not dry:
            shutil.copytree(src_path, dst_path, dirs_exist_ok=True)


def symlink(src: str, dst: str, dry: bool):
    """Symlink `src` to `dst`, printing details.

    Work on a file or a directory.  Expand "~" to home directory.  Overwrite
    existing file(s).

    On Windows, the user may don't have the privilege to create symbolic links,
    so instead of symlinking the file is copied.

    :param src: The source.
    :param dst: The destination.
    :param dry: If True, perform a dry run.
    """
    if platform.system() == "Windows":
        copy(src, dst, dry)
    else:
        _do_symlink(src, dst, dry)


def _do_symlink(src: str, dst: str, dry: bool):
    """Symlink `src` to `dst`, printing details.

    This is used internally in `symlink`.
    """
    # Convert to Path objects.
    src_path = Path(src).expanduser()
    dst_path = Path(dst).expanduser()

    # Raise error if src does not exist.
    if not src_path.exists():
        raise FileNotFoundError

    # Make the simbolic link.
    print(f"Symlinking {cyan(src_path)} as {cyan(dst_path)}.")
    if not dry:
        dst_path.unlink(missing_ok=True)
        src_path = src_path.absolute()
        dst_path.symlink_to(src_path, target_is_directory=src_path.is_dir())


def dconf_load(src: str, dst: str, dry: bool):
    """Load dconf configuration from src to dst.

    If dry is True, perform a dry run.

    Return the return code of the dconf process, or 0 if dry is True.
    """
    # Convert src to Path object.
    src_path = Path(src).expanduser()

    # Raise error if src does not exist.
    if not src_path.exists():
        raise FileNotFoundError

    # Load with dconf.
    print(f"Loading {cyan(src_path)} to dconf path {cyan(dst)}.")
    if dry:
        return 0
    with open(src_path, "rb") as src_fd:
        cmd = ["dconf", "load", dst]
        proc = subprocess.run(cmd, stdin=src_fd)
        return proc.returncode


if __name__ == "__main__":
    # Parse arguments.
    import argparse

    parser = argparse.ArgumentParser(
        description="Installation script for Unix dotfiles."
    )
    parser.add_argument("--dry", action="store_true", help="perform a dry run")
    args = parser.parse_args()
    dry = args.dry

    # OS constants.
    WINDOWS = platform.system() == "Windows"
    LINUX = platform.system() == "Linux"
    WSL = "WSL_DISTRO_NAME" in os.environ

    # Make sure the script is run in the correct directory.
    try:
        setup_directory()
    except DirectoryError:
        print("The script cannot find the correct directory to run.")
        sys.exit(1)

    # Install dot files.
    copy("./dot_gitconfig", "~/.gitconfig", dry)
    copy("./mypy", "~/.config/mypy", dry)
    if WINDOWS:
        copy(
            "./Microsoft.PowerShell_profile.ps1",
            "~/Documents/WindowsPowerShell/Microsoft.PowerShell_profile.ps1",
            dry,
        )
        # TODO Install Rime config for Windows, and remove standalone install
        # scripts.
        #
        # TODO Install AutoHotkey scripts.
    if LINUX:
        copy("./dot_bashrc", "~/.bashrc", dry)
        copy("./dot_bash_profile", "~/.bash_profile", dry)
        copy("./fonts.conf", "~/.config/fontconfig/fonts.conf", dry)
        copy("./fcitx5", "~/.config/fcitx5", dry)
        copy("./rime", "~/.local/share/fcitx5/rime", dry)
        copy("./xremap", "~/.config/xremap", dry)

    # Load dconf.
    if LINUX and shutil.which("dconf"):
        dconf_load("./gnome_dconf/wm.dconf", "/org/gnome/desktop/wm/", dry)
        dconf_load("./gnome_dconf/mutter.dconf", "/org/gnome/mutter/", dry)
        dconf_load(
            "./gnome_dconf/media-keys.dconf",
            "/org/gnome/settings-daemon/media-keys/",
            dry,
        )
        dconf_load(
            "./gnome_dconf/dash-to-dock.dconf",
            "/org/gnome/shell/extensions/dash-to-dock/",
            dry,
        )
    else:
        print("Skipping dconf configuration.")

    # Symlinking (or copying) scripts.
    if WSL:
        symlink("./scripts/wsl-emacs", "~/.local/bin/wsl-emacs", dry)
