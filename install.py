#!/usr/bin/python3
"""Cross-platform installation script for my dotfiles."""

from abc import ABC, abstractmethod
import argparse
import logging
import os
import platform
import shutil
from pathlib import Path
from typing import Union


def setup_logging(debug: bool = False):
    """Set up logging."""
    if debug:
        logging.getLogger().setLevel(logging.DEBUG)


def pathify(s: Union[str, os.PathLike]) -> Path:
    """Convert `s` to an absolute `Path` object.

    Expand "~" (user home) and env vars in the process.
    """
    s = os.path.expandvars(s)
    path = Path(s).expanduser().absolute()
    return path


def already_linked(src: Path, dst: Path) -> bool:
    """Return True if `dst` points to `src`."""
    if dst.is_symlink():
        try:
            return dst.resolve().samefile(src)
        except Exception:
            return False
    return False


def link_rec(src: Path, dst: Path) -> None:
    """Symlink `dst` to `src` recursively without checking."""
    if src.is_file():
        if already_linked(src, dst):
            logging.debug("skip existing '%s'", dst)
            return
        elif dst.is_symlink() or dst.exists():
            logging.debug("remove incorrect '%s'", dst)
            dst.unlink()
        logging.debug("creating symlink '%s'", dst)
        dst.symlink_to(src)
    else:
        dst.mkdir(exist_ok=True)
        for s in src.iterdir():
            d = dst.joinpath(s.name)
            link_rec(s, d)


def is_newer(src: Path, dst: Path) -> bool:
    """Returns `True` if `src` is newer than `dst`."""
    src_mtime = src.stat().st_mtime
    dst_mtime = dst.stat().st_mtime
    return src_mtime > dst_mtime


def copy_rec(src: Path, dst: Path) -> None:
    """Copy `src` to `dst` recursively without checking."""
    if src.is_file():
        if not dst.exists() or is_newer(src, dst):
            shutil.copyfile(src, dst)
            logging.debug("copying file to '%s'", dst)
        else:
            logging.debug("skip existing '%s'", dst)
    else:
        dst.mkdir(exist_ok=True)
        for s in src.iterdir():
            d = dst.joinpath(s.name)
            copy_rec(s, d)


def link(
    src: Union[str, os.PathLike], dst: Union[str, os.PathLike], mkdir: bool = False
) -> None:
    """Symlink `dst` to `src`.

    On Windows, this function copies files instead.
    """
    # Pathify arguments
    src_p, dst_p = pathify(src), pathify(dst)
    # Validate `src`
    if not src_p.exists():
        raise FileNotFoundError(f"'{src_p}' does not exist")
    # Make sure `dst`'s parent exists
    dst_p.parent.mkdir(parents=True, exist_ok=True)
    # Make symlink(s) or copy the files
    if platform.system() == "Windows":
        copy_rec(src_p, dst_p)
    else:
        link_rec(src_p, dst_p)


class Task(ABC):
    """A task to perform."""

    @abstractmethod
    def run(self) -> str | None:
        """Perform the task. Returns an optional hint string."""


class Kitty(Task):
    """Install kitty config."""

    def run(self) -> str | None:
        link("./apps/kitty", "~/.config/kitty")


class Git(Task):
    """Install git config."""

    def run(self) -> str | None:
        link("./apps/git/gitconfig", "~/.gitconfig")


class Rime(Task):
    """Install rime config."""

    def run(self) -> str | None:
        rime_dir = pathify("~/Library/Rime")
        # Check missing schemas if not on Windows
        if platform.system() != "Windows":
            schemas = ["cangjie5", "quick5"]
            missing_schemas = []
            for schema in schemas:
                schema_file = rime_dir.joinpath(f"{schema}.schema.yaml")
                if not schema_file.exists():
                    missing_schemas.append(schema)
            if missing_schemas:
                raise RuntimeError(
                    "schema(s) missing: {}".format(", ".join(missing_schemas))
                )
        # Install dotfiles
        link("./apps/rime", rime_dir)


class Zsh(Task):
    """Install zsh config."""

    def run(self) -> str | None:
        link("./apps/zsh/zshenv", "~/.zshenv")
        link("./apps/zsh/zshrc", "~/.zshrc")
        link("./apps/zsh/p10k.zsh", "~/.p10k.zsh")
        if not os.environ.get("SHELL", "").endswith("zsh"):
            return "Consider setting zsh as your default shell."


class PowerShell(Task):
    """Install PowerShell config."""

    def run(self) -> str | None:
        link(
            "./apps/PowerShell/Microsoft.PowerShell_profile.ps1",
            "~/Documents/WindowsPowerShell/Microsoft.PowerShell_profile.ps1",
        )


if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Install Zyxir's dotfiles.")
    parser.add_argument("--debug", help="turn on debug mode", action="store_true")
    args = parser.parse_args()
    debug: bool = args.debug

    # Setup logging
    setup_logging(debug=debug)

    # Define platform-specific tasks
    tasks: list[Task] = []
    if platform.system() == "Darwin":
        tasks += [Git(), Kitty(), Rime(), Zsh()]
    elif platform.system() == "Windows":
        tasks += [Git(), Rime(), PowerShell()]

    # Perform the tasks
    for task in tasks:
        print("{}..".format(task.__doc__), end="")
        try:
            hint = task.run()
            print("\033[1;32m\u2713\033[0m")
            if hint:
                print(f"\u2757{hint}")
        except Exception as e:
            print(f"\033[1;31m\u2717\033[0m \033[33m{e}\033[0m")
