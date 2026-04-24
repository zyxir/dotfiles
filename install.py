#!/usr/bin/python3
"""Cross-platform installation script for my dotfiles."""

from __future__ import annotations

import argparse
import logging
import os
import platform
import shutil
import subprocess
import tempfile
import urllib.request
import zipfile
from abc import ABC, abstractmethod
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
        try:
            dst.symlink_to(src)
        except OSError as e:
            if getattr(e, "winerror", None) == 1314:
                raise PermissionError(
                    "Cannot create symlinks. Either:\n"
                    "  • Enable Developer Mode: Settings → Privacy & Security → For Developers\n"
                    "  • Or re-run this script as Administrator"
                ) from e
            raise
    else:
        dst.mkdir(exist_ok=True)
        for s in src.iterdir():
            d = dst.joinpath(s.name)
            link_rec(s, d)


def cleanup_dead_symlinks(path: Path) -> None:
    """Remove all dead symlinks in a directory recursively."""
    if not path.is_dir():
        return
    for entry in path.rglob("*"):
        if entry.is_symlink() and not entry.exists():
            logging.debug("remove dead symlink '%s'", entry)
            entry.unlink()


def link(
    src: Union[str, os.PathLike], dst: Union[str, os.PathLike], mkdir: bool = False
) -> None:
    """Symlink `dst` to `src`.

    On Windows, this requires Developer Mode or Administrator privileges.
    If `dst` is a directory, removes any dead symlinks after symlinking.
    """
    # Pathify arguments
    src_p, dst_p = pathify(src), pathify(dst)
    # Validate `src`
    if not src_p.exists():
        raise FileNotFoundError(f"'{src_p}' does not exist")
    # Make sure `dst`'s parent exists
    dst_p.parent.mkdir(parents=True, exist_ok=True)
    # Make symlink(s)
    link_rec(src_p, dst_p)
    # Clean up dead symlinks if destination is a directory
    if src_p.is_dir():
        cleanup_dead_symlinks(dst_p)


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


RIME_SCHEMA_FILES: list[tuple[str, str]] = [
    # (filename, url)
    ("cangjie5.schema.yaml", "https://raw.githubusercontent.com/rime/rime-cangjie/master/cangjie5.schema.yaml"),
    ("cangjie5.dict.yaml", "https://raw.githubusercontent.com/rime/rime-cangjie/master/cangjie5.dict.yaml"),
    ("quick5.schema.yaml", "https://raw.githubusercontent.com/rime/rime-quick/master/quick5.schema.yaml"),
    ("quick5.dict.yaml", "https://raw.githubusercontent.com/rime/rime-quick/master/quick5.dict.yaml"),
    ("double_pinyin.schema.yaml", "https://raw.githubusercontent.com/rime/rime-double-pinyin/master/double_pinyin.schema.yaml"),
]


class Rime(Task):
    """Install rime config."""

    def run(self) -> str | None:
        rime_dir = pathify("~/Library/Rime")
        # Download missing schemas if not on Windows
        downloaded: list[str] = []
        if platform.system() != "Windows":
            rime_dir.mkdir(parents=True, exist_ok=True)
            for filename, url in RIME_SCHEMA_FILES:
                dst = rime_dir / filename
                if dst.exists():
                    continue
                logging.debug("downloading rime file: %s", filename)
                urllib.request.urlretrieve(url, dst)
                downloaded.append(filename)
        # Install dotfiles
        link("./apps/rime", rime_dir)
        if downloaded:
            return f"Downloaded {len(downloaded)} schema file(s): {', '.join(downloaded)}."


class Zsh(Task):
    """Install zsh config."""

    def run(self) -> str | None:
        link("./apps/zsh/zshenv", "~/.zshenv")
        link("./apps/zsh/zshrc", "~/.zshrc")
        link("./apps/zsh/p10k.zsh", "~/.p10k.zsh")
        secrets_file = pathify("~/.zshenv.secrets")
        if not secrets_file.exists():
            return "❗Create ~/.zshenv.secrets for secrets (e.g. ANTHROPIC_AUTH_TOKEN)."
        if not os.environ.get("SHELL", "").endswith("zsh"):
            return "❗Consider setting zsh as your default shell."


class PowerShell(Task):
    """Install PowerShell config."""

    def run(self) -> str | None:
        link(
            "./apps/PowerShell/Microsoft.PowerShell_profile.ps1",
            "~/Documents/WindowsPowerShell/Microsoft.PowerShell_profile.ps1",
        )


class ClaudeCode(Task):
    """Install Claude Code config."""

    def run(self) -> str | None:
        link("./apps/claude-code/settings.json", "~/.claude/settings.json")
        if not os.environ.get("ANTHROPIC_AUTH_TOKEN"):
            return (
                "❗Add ANTHROPIC_AUTH_TOKEN to ~/.zshenv.secrets and reload your shell."
            )


def _system_font_dir() -> Path:
    """Return the platform-specific system fonts directory."""
    if platform.system() == "Darwin":
        return pathify("~/Library/Fonts")
    return pathify("~/AppData/Local/Microsoft/Windows/Fonts")


def install_fonts(base_url: str, files: list[str]) -> list[str]:
    """Download missing fonts from direct URLs.

    Returns the list of filenames that were actually installed.
    """
    font_dir = _system_font_dir()
    font_dir.mkdir(parents=True, exist_ok=True)

    installed: list[str] = []
    for filename in files:
        dst = font_dir / filename
        if dst.exists():
            logging.debug("font already installed: %s", filename)
            continue
        url = base_url + filename.replace(" ", "%20")
        logging.debug("downloading font: %s", filename)
        urllib.request.urlretrieve(url, dst)
        installed.append(filename)
    return installed


def install_fonts_from_zip(url: str) -> list[str]:
    """Download and extract missing fonts from a zip archive.

    Returns the list of filenames that were actually installed.
    """
    font_dir = _system_font_dir()
    font_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp:
        urllib.request.urlretrieve(url, tmp.name)
        tmp_path = Path(tmp.name)

    try:
        with tempfile.TemporaryDirectory() as extract_dir:
            with zipfile.ZipFile(tmp_path, "r") as zf:
                zf.extractall(extract_dir)

            installed: list[str] = []
            for ext in ("*.otf", "*.ttf"):
                for src in Path(extract_dir).rglob(ext):
                    dst = font_dir / src.name
                    if dst.exists():
                        logging.debug("font already installed: %s", src.name)
                        continue
                    logging.debug("installing font: %s", src.name)
                    shutil.copy2(src, dst)
                    installed.append(src.name)
    finally:
        tmp_path.unlink()

    return installed


class MesloLGSFont(Task):
    """Install MesloLGS NF font."""

    def run(self) -> str | None:
        installed = install_fonts(
            "https://raw.githubusercontent.com/romkatv/powerlevel10k-media/master/",
            [
                "MesloLGS NF Regular.ttf",
                "MesloLGS NF Bold.ttf",
                "MesloLGS NF Italic.ttf",
                "MesloLGS NF Bold Italic.ttf",
            ],
        )
        if installed:
            return f"Installed {len(installed)} file(s): {', '.join(installed)}."


class SourceHanSansFont(Task):
    """Install Source Han Sans font."""

    def run(self) -> str | None:
        installed = install_fonts_from_zip(
            "https://github.com/adobe-fonts/source-han-sans/"
            "releases/download/2.005R/09_SourceHanSansSC.zip"
        )
        if installed:
            return f"Installed {len(installed)} file(s): {', '.join(installed)}."


class VSCodium(Task):
    """Install VSCodium config and extensions."""

    def run(self) -> str | None:
        if platform.system() == "Darwin":
            user_dir = "~/Library/Application Support/VSCodium/User"
        else:
            user_dir = "~/AppData/Roaming/VSCodium/User"
        link("./apps/vscodium/settings.json", f"{user_dir}/settings.json")

        codium = shutil.which("codium")
        if codium is None:
            return "❗Install VSCodium to sync extensions (codium CLI not found)."

        extensions_file = pathify("./apps/vscodium/extensions.txt")
        wanted = [
            line.strip()
            for line in extensions_file.read_text().splitlines()
            if line.strip() and not line.startswith("#")
        ]
        installed = set(
            subprocess.run(
                [codium, "--list-extensions"],
                capture_output=True,
                text=True,
                check=True,
            ).stdout.split()
        )
        missing = [ext for ext in wanted if ext not in installed]
        for ext in missing:
            logging.debug("installing extension %s", ext)
            subprocess.run(
                [codium, "--install-extension", ext, "--force"],
                capture_output=True,
                check=True,
            )
        if missing:
            return (
                f"Installed {len(missing)} VSCodium extension(s): {', '.join(missing)}"
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
        tasks += [
            Git(),
            Kitty(),
            Rime(),
            Zsh(),
            ClaudeCode(),
            VSCodium(),
            MesloLGSFont(),
            SourceHanSansFont(),
        ]
    elif platform.system() == "Windows":
        tasks += [
            Git(),
            Rime(),
            PowerShell(),
            ClaudeCode(),
            VSCodium(),
            MesloLGSFont(),
            SourceHanSansFont(),
        ]

    # Perform the tasks
    for task in tasks:
        print("{}..".format(task.__doc__), end="", flush=True)
        try:
            hint = task.run()
            print("\033[1;32m\u2713\033[0m")
            if hint:
                print(hint)
        except Exception as e:
            print(f"\033[1;31m\u2717\033[0m \033[33m{e}\033[0m")
