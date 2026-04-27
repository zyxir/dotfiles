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
from collections.abc import Callable
from pathlib import Path
from typing import Union


class _DebugTracker(logging.Handler):
    """Logging handler that records whether any debug message was emitted."""

    def __init__(self) -> None:
        super().__init__(logging.DEBUG)
        self.fired = False

    def reset(self) -> None:
        self.fired = False

    def emit(self, record: logging.LogRecord) -> None:
        self.fired = True


def setup_logging(debug: bool = False) -> _DebugTracker:
    """Set up logging. Returns a tracker that detects debug output."""
    tracker = _DebugTracker()
    logging.getLogger().addHandler(tracker)
    if debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logging.basicConfig(level=logging.DEBUG)
    return tracker


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


def link_rec(src: Path, dst: Path) -> bool:
    """Symlink `dst` to `src` recursively without checking. Returns True if any symlink was created."""
    if src.is_file():
        if already_linked(src, dst):
            logging.debug("skip existing '%s'", dst)
            return False
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
        return True
    else:
        dst.mkdir(exist_ok=True)
        return any(link_rec(s, dst.joinpath(s.name)) for s in src.iterdir())


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
) -> bool:
    """Symlink `dst` to `src`. Returns True if any symlink was created.

    On Windows, this requires Developer Mode or Administrator privileges.
    If `dst` is a directory, removes any dead symlinks after symlinking.
    """
    src_p, dst_p = pathify(src), pathify(dst)
    if not src_p.exists():
        raise FileNotFoundError(f"'{src_p}' does not exist")
    dst_p.parent.mkdir(parents=True, exist_ok=True)
    created = link_rec(src_p, dst_p)
    if src_p.is_dir():
        cleanup_dead_symlinks(dst_p)
    return created


class _Skipped:
    pass


SKIPPED = _Skipped()


class Step:
    """A named sub-action within a task."""

    def __init__(self, description: str, fn: Callable[[], str | _Skipped | None]):
        self.description = description
        self._fn = fn

    def run(self) -> str | _Skipped | None:
        return self._fn()


class Task(ABC):
    """A task to perform."""

    @abstractmethod
    def steps(self) -> list[Step]:
        """Return the list of steps that make up this task."""


class Git(Task):
    """Install git config."""

    def steps(self) -> list[Step]:
        return [Step("Link ~/.gitconfig", self._run)]

    def _run(self) -> str | _Skipped | None:
        if not link("./apps/git/gitconfig", "~/.gitconfig"):
            return SKIPPED


PLUM_URL = "https://github.com/rime/plum.git"
# (plum schema name, sentinel file installed by plum)
PLUM_SCHEMAS: list[tuple[list[str], str, str | None]] = [
    (["iDvel/rime-ice:others/recipes/full", "iDvel/rime-ice:others/recipes/config:schema=double_pinyin"], "rime_ice.schema.yaml", "rime-ice"),
    (["cangjie"], "cangjie5.schema.yaml", None),
    (["quick"], "quick5.schema.yaml", None),
]


class Rime(Task):
    """Install rime config."""

    def steps(self) -> list[Step]:
        return [
            Step("Clone plum into Rime directory", self._install_plum),
            *[Step(f"Install schema: {name or pkgs[0]}", self._schema_installer(pkgs, sentinel)) for pkgs, sentinel, name in PLUM_SCHEMAS],
            Step("Link config", self._run),
        ]

    def _schema_installer(self, packages: list[str], sentinel: str) -> Callable[[], str | _Skipped | None]:
        def _install() -> str | _Skipped | None:
            if platform.system() == "Windows":
                return SKIPPED
            rime_dir = pathify("~/Library/Rime")
            if (rime_dir / sentinel).exists():
                return SKIPPED
            rime_install = rime_dir / "plum" / "rime-install"
            for pkg in packages:
                logging.debug("installing schema: %s", pkg)
                subprocess.run(
                    ["bash", str(rime_install), pkg],
                    check=True,
                    capture_output=True,
                    env={**os.environ, "rime_dir": str(rime_dir)},
                )
        return _install

    def _install_plum(self) -> str | _Skipped | None:
        if platform.system() == "Windows":
            return SKIPPED
        dst = pathify("~/Library/Rime/plum")
        if dst.exists():
            return SKIPPED
        logging.debug("cloning plum into %s", dst)
        subprocess.run(
            ["git", "clone", "--depth", "1", PLUM_URL, str(dst)],
            check=True,
            capture_output=True,
        )

    def _run(self) -> str | _Skipped | None:
        rime_dir = pathify("~/Library/Rime")
        created = link("./apps/rime", rime_dir)
        if not created:
            return SKIPPED


class Zsh(Task):
    """Install zsh config."""

    def steps(self) -> list[Step]:
        return [Step("Link config files", self._run)]

    def _run(self) -> str | _Skipped | None:
        a = link("./apps/zsh/zshenv", "~/.zshenv")
        b = link("./apps/zsh/zshrc", "~/.zshrc")
        c = link("./apps/zsh/p10k.zsh", "~/.p10k.zsh")
        secrets_file = pathify("~/.zshenv.secrets")
        if not secrets_file.exists():
            return "❗Create ~/.zshenv.secrets for secrets (e.g. ANTHROPIC_AUTH_TOKEN)."
        if not os.environ.get("SHELL", "").endswith("zsh"):
            return "❗Consider setting zsh as your default shell."
        if not (a or b or c):
            return SKIPPED


class PowerShell(Task):
    """Install PowerShell config."""

    def steps(self) -> list[Step]:
        return [Step("Link profile", self._run)]

    def _run(self) -> str | _Skipped | None:
        if not link(
            "./apps/PowerShell/Microsoft.PowerShell_profile.ps1",
            "~/Documents/WindowsPowerShell/Microsoft.PowerShell_profile.ps1",
        ):
            return SKIPPED


class ClaudeCode(Task):
    """Install Claude Code config."""

    def steps(self) -> list[Step]:
        return [Step("Link settings.json", self._run)]

    def _run(self) -> str | _Skipped | None:
        created = link("./apps/claude-code/settings.json", "~/.claude/settings.json")
        if not os.environ.get("ANTHROPIC_AUTH_TOKEN"):
            return "❗Add ANTHROPIC_AUTH_TOKEN to ~/.zshenv.secrets and reload your shell."
        if not created:
            return SKIPPED


def _system_font_dir() -> Path:
    """Return the platform-specific system fonts directory."""
    if platform.system() == "Darwin":
        return pathify("~/Library/Fonts")
    return pathify("~/AppData/Local/Microsoft/Windows/Fonts")


def install_fonts_from_zip(url: str, filenames: list[str] | None = None) -> list[str]:
    """Download and extract missing fonts from a zip archive.

    Returns the list of filenames that were actually installed.
    """
    font_dir = _system_font_dir()
    font_dir.mkdir(parents=True, exist_ok=True)

    if filenames is not None and all((font_dir / f).exists() for f in filenames):
        logging.debug("all fonts already installed, skipping download")
        return []

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
                    if filenames is not None and src.name not in filenames:
                        continue
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


class Fonts(Task):
    """Install fonts."""

    def steps(self) -> list[Step]:
        return [
            Step("JetBrainsMono Nerd Font", self._jetbrains_mono),
            Step("Source Han Sans", self._source_han_sans),
        ]

    def _jetbrains_mono(self) -> str | _Skipped | None:
        installed = install_fonts_from_zip(
            "https://github.com/ryanoasis/nerd-fonts/releases/latest/download/JetBrainsMono.zip",
            [
                "JetBrainsMonoNerdFontMono-Regular.ttf",
                "JetBrainsMonoNerdFontMono-Bold.ttf",
                "JetBrainsMonoNerdFontMono-Italic.ttf",
                "JetBrainsMonoNerdFontMono-BoldItalic.ttf",
            ],
        )
        if not installed:
            return SKIPPED
        return f"Installed {len(installed)} file(s): {', '.join(installed)}."

    def _source_han_sans(self) -> str | _Skipped | None:
        installed = install_fonts_from_zip(
            "https://github.com/adobe-fonts/source-han-sans/"
            "releases/download/2.005R/09_SourceHanSansSC.zip",
            [
                "SourceHanSansSC-ExtraLight.otf",
                "SourceHanSansSC-Light.otf",
                "SourceHanSansSC-Normal.otf",
                "SourceHanSansSC-Regular.otf",
                "SourceHanSansSC-Medium.otf",
                "SourceHanSansSC-Bold.otf",
                "SourceHanSansSC-Heavy.otf",
            ],
        )
        if not installed:
            return SKIPPED
        return f"Installed {len(installed)} file(s): {', '.join(installed)}."


class Ghostty(Task):
    """Install Ghostty config."""

    def steps(self) -> list[Step]:
        return [Step("Link ~/.config/ghostty", self._run)]

    def _run(self) -> str | _Skipped | None:
        if not link("./apps/ghostty", "~/.config/ghostty"):
            return SKIPPED


class VSCodium(Task):
    """Install VSCodium config and extensions."""

    def steps(self) -> list[Step]:
        return [
            Step("Link settings.json", self._link_settings),
            Step("Install extensions", self._install_extensions),
        ]

    def _link_settings(self) -> str | _Skipped | None:
        if platform.system() == "Darwin":
            user_dir = "~/Library/Application Support/VSCodium/User"
        else:
            user_dir = "~/AppData/Roaming/VSCodium/User"
        if not link("./apps/vscodium/settings.json", f"{user_dir}/settings.json"):
            return SKIPPED

    def _install_extensions(self) -> str | _Skipped | None:
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
        if not missing:
            return SKIPPED
        for ext in missing:
            logging.debug("installing extension %s", ext)
            subprocess.run(
                [codium, "--install-extension", ext, "--force"],
                capture_output=True,
                check=True,
            )
        if missing:
            return f"Installed {len(missing)} VSCodium extension(s): {', '.join(missing)}"


if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Install Zyxir's dotfiles.")
    parser.add_argument("--debug", help="turn on debug mode", action="store_true")
    args = parser.parse_args()
    debug: bool = args.debug

    # Setup logging
    tracker = setup_logging(debug=debug)

    # Define platform-specific tasks
    tasks: list[Task] = []
    if platform.system() == "Darwin":
        tasks += [
            Git(),
            Ghostty(),
            Rime(),
            Zsh(),
            ClaudeCode(),
            VSCodium(),
            Fonts(),
        ]
    elif platform.system() == "Windows":
        tasks += [
            Git(),
            Rime(),
            PowerShell(),
            ClaudeCode(),
            VSCodium(),
            Fonts(),
        ]

    # Perform the tasks
    for task in tasks:
        print("- {}...".format(task.__doc__), flush=True)
        try:
            for step in task.steps():
                label = "  + {}...".format(step.description)
                print(label, flush=True)
                tracker.reset()
                result = step.run()
                if isinstance(result, _Skipped):
                    status = "\033[0;33mSKIP\033[0m"
                    hint = None
                else:
                    status = "\033[1;32mDONE\033[0m"
                    hint = result
                if tracker.fired:
                    print("  " + status)
                else:
                    print("\033[1A\r{} {}".format(label, status))
                if hint:
                    print(hint)
        except Exception as e:
            print("  \033[1;31mFAILED\033[0m \033[33m{}\033[0m".format(e))
