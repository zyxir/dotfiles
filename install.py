#!/usr/bin/python3
"""Cross-platform installation script for my dotfiles."""

from abc import ABC, abstractmethod
import argparse
import logging
import os
import platform
from pathlib import Path
from typing import Union


def setup_logging(debug: bool = False):
    """Set up logging."""
    if debug:
        logging.getLogger().setLevel(logging.DEBUG)


def pathify(s: Union[str, os.PathLike]) -> Path:
    """Convert `s` to an absolute `Path` object.

    Expand "~" to user home directory in the process.
    """
    s = os.path.expandvars(s)
    path = Path(s).expanduser().absolute()
    return path


def _link_rec(src: Path, dst: Path) -> None:
    """Symlink `dst` to `src` recursively without checking."""
    if src.is_file():
        if dst.is_symlink() and dst.resolve().samefile(src):
            logging.debug("skip existing '%s'", dst)
            return
        elif dst.exists():
            logging.debug("remove incorrect '%s'", dst)
            dst.unlink()
        logging.debug("creating symlink '%s'", dst)
        dst.symlink_to(src)
    else:
        dst.mkdir(exist_ok=True)
        for s in src.iterdir():
            d = dst.joinpath(s.name)
            _link_rec(s, d)


def link(
    src: Union[str, os.PathLike], dst: Union[str, os.PathLike], mkdir: bool = False
) -> None:
    """Symlink `dst` to `src`."""
    # Pathify arguments
    src_p, dst_p = pathify(src), pathify(dst)
    # Validate `src`
    if not src_p.exists():
        raise FileExistsError(f"'{src_p}' does not exist")
    # Make sure `dst`'s parent exists
    dst_p.parent.mkdir(parents=True, exist_ok=True)
    # Make symlink(s)
    _link_rec(src_p, dst_p)


class Result:
    """Installation result."""

    hint: str = ""


class Success(Result):
    """A success."""

    def __init__(self, hint: str = "") -> None:
        self.hint = hint


class Failure(Result):
    """A failure."""

    def __init__(self, msg: str, hint: str = "") -> None:
        self.msg = msg
        self.hint = hint


class Task(ABC):
    """A task to perform."""

    @abstractmethod
    def run(self) -> Result:
        """Perform the task."""


class Kitty(Task):
    """Install kitty config."""

    def run(self) -> Result:
        link("./apps/kitty", "~/.config/kitty")
        return Success()


class Git(Task):
    """Install git config."""

    def run(self) -> Result:
        link("./apps/git/gitconfig", "~/.gitconfig")
        return Success()


class Rime(Task):
    """Install rime config."""

    def run(self) -> Result:
        rime_dir = pathify("~/Library/Rime")
        # Check missing schemas
        schemas = ["cangjie5", "double_pinyin_flypy", "pinyin_simp"]
        missing_schemas = []
        for schema in schemas:
            schema_file = rime_dir.joinpath(f"{schema}.schema.yaml")
            if not schema_file.exists():
                missing_schemas.append(schema)
        if missing_schemas:
            return Failure("schema(s) missing: {}".format(", ".join(missing_schemas)))
        # Install dotfiles
        link("./apps/rime", rime_dir)
        return Success()


class Zsh(Task):
    """Install zsh config."""

    def run(self) -> Result:
        link("./apps/zsh/zshenv", "~/.zshenv")
        link("./apps/zsh/zshrc", "~/.zshrc")
        link("./apps/zsh/p10k.zsh", "~/.p10k.zsh")
        result = Success()
        if not os.environ.get("SHELL", "").endswith("zsh"):
            result.hint = "Consider setting zsh as your default shell."
        return result


if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Install Zyxir's dotfiles.")

    # Setup logging
    setup_logging(debug=False)

    # Define platform-specific tasks
    tasks: list[Task] = []
    if platform.system() == "Darwin":
        tasks += [Git(), Kitty(), Rime(), Zsh()]

    # Perform the tasks
    for task in tasks:
        print("{}..".format(task.__doc__), end="")
        result = task.run()
        if isinstance(result, Success):
            print("\033[1;32m\u2713\033[0m")
        elif isinstance(result, Failure):
            print(f"\033[1;31m\u2717\033[0m \033[33m{result.msg}\033[0m")
        if result.hint != "":
            print(f"\u2757{result.hint}")
