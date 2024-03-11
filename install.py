#!/bin/python3
"""Cross-platform installation script for my dotfiles."""

import os
import platform
import shlex
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import List, Optional, Union


# OS constants.
WINDOWS = platform.system() == "Windows"
LINUX = platform.system() == "Linux"
WSL = "WSL" in platform.uname().release


def cyan(path: Union[str, Path]) -> str:
    """Wrap path in cyan ANSI escape codes."""
    return "\u001b[36m" + str(path) + "\u001b[0m"


def red(path: Union[str, Path]) -> str:
    """Wrap path in red ANSI escape codes."""
    return "\u001b[31m" + str(path) + "\u001b[0m"


class DirectoryError(Exception):
    """Raised when the script cannot be executed in the correct directory."""

    pass


def normalize_path(p: Union[str, Path]) -> Path:
    """Normalize path."""
    if isinstance(p, str):
        normalized = Path(os.path.expandvars(p)).expanduser()
    else:
        normalized = p.expanduser()
    normalized = normalized.absolute()
    return normalized


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
    src_path = normalize_path(src)
    dst_path = normalize_path(dst)

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
    if WINDOWS:
        copy(src, dst, dry)
    else:
        _do_symlink(src, dst, dry)


def _do_symlink(src: str, dst: str, dry: bool):
    """Symlink `src` to `dst`, printing details.

    This is used internally in `symlink`.
    """
    # Convert to Path objects.
    src_path = normalize_path(src)
    dst_path = normalize_path(dst)

    # Raise error if src does not exist.
    if not src_path.exists():
        raise FileNotFoundError

    # Make the simbolic link.
    print(f"Symlinking {cyan(src_path)} as {cyan(dst_path)}.")
    if not dry:
        dst_path.unlink(missing_ok=True)
        src_path = src_path.absolute()
        dst_path.symlink_to(src_path, target_is_directory=src_path.is_dir())


def ahk_compile(src: str, dry: bool):
    """Compile AutoHotkey scripts and add them to startup.

    If dry is True, perform a dry run.

    Return the return code of the dconf process, or 0 if dry is True.
    """
    # Convert to Path object.
    src_path = normalize_path(src)

    # Compile every .ahk file.
    for f in src_path.glob("*.ahk"):
        _ahk_compile(f, dry)


def _ahk_compile(src: Path, dry: bool):
    """Compile one AutoHotkey script and add it to startup."""
    # Move it to startup.
    src_exe = src.parent.joinpath(src.stem + ".exe")
    startup_dir = os.path.expandvars(
        "%appdata%/Microsoft/Windows/Start Menu/Programs/Startup"
    )
    print(f"Adding {cyan(src_exe)} to startup.")
    if not dry and not Path(startup_dir).joinpath(src_exe.name).exists():
        compiler_path = "C:\\Program Files\\AutoHotkey\\Compiler\\Ahk2Exe.exe"
        if Path(compiler_path).exists():
            cmd = [compiler_path, "/in", str(src)]
            subprocess.run(cmd)
            shutil.copy(src_exe, startup_dir)
        else:
            shutil.copy(src, startup_dir)


def dconf_load(src: str, dst: str, dry: bool) -> int:
    """Load dconf configuration from src to dst.

    If dry is True, perform a dry run.

    Return the return code of the dconf process, or 0 if dry is True.
    """
    # Convert src to Path object.
    src_path = normalize_path(src)

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


def run_command(
    cmd: str,
    msg: str,
    dry: bool,
    workdir: Optional[Path] = None,
    shell: bool = False,
) -> int:
    """Run command cmd and print msg, return the return code.

    If dry is True, perform a dry run.

    Use the current directory by default, or workdir if given.  Argument shell
    is passed to subprocess.run().

    stdout and stderr are captured and logged.
    """
    print(msg)
    if not dry:
        # Go to target dir.
        cwd = normalize_path(workdir if workdir is not None else os.getcwd())
        if workdir:
            os.chdir(workdir)
        # Run command.
        args = shlex.split(cmd)
        proc = subprocess.run(args, capture_output=True, text=True, shell=shell)
        code = proc.returncode
        # Get back.
        if workdir:
            os.chdir(cwd)
        # Return the return code.
        return code
    return 0


def linux_configure_rime(dry: bool):
    """Configure Rime on Linux.

    If dry is True, perform a dry run.
    """
    if not dry:
        src = "./apps/rime/default.custom.linux.yaml"
        dst = os.path.expanduser("~/.local/share/fcitx5/rime/default.custom.yaml")
        if os.path.exists(dst):
            os.remove(dst)
        shutil.copy(src, dst)


def windows_configure_cangjie6(dry: bool):
    """Configure the Cangjie6 schema of Rime on Windows.

    If dry is True, perform a dry run.
    """
    custom = normalize_path("%appdata%/rime/cangjie6.custom.yaml")
    content = """patch:
  "switches/@2/reset": 1
    """
    print(f"Creating {cyan(custom)} for Windows.")
    if not dry:
        with open(custom, "w") as fp:
            fp.write(content)


def first_existing_path(*paths: str) -> Optional[str]:
    """Return the first path available."""
    for path in paths:
        if normalize_path(path).exists():
            return path
    return None


def install_fonts(dry: bool):
    """Install fonts from font_zip, a zip file containing all fonts wanted.

    If dry is True, perform a dry run.
    """
    font_zip_path = first_existing_path(
        "~/Zyspace/pcsetup/ZyFonts.zip",
        "/mnt/c/Users/zyxir/Zyspace/pcsetup/ZyFonts.zip",
        "~/Downloads/ZyFonts.zip",
        "/media/zyxir/Zydisk/pcsetup/ZyFonts.zip"
    )
    if font_zip_path is None:
        print("Skip font installation as no ZyFonts.zip is found.")
        return
    print(f"Installing fonts in {cyan(font_zip_path)}.")
    if not dry:
        font_zip = zipfile.ZipFile(normalize_path(font_zip_path), "r")
        with tempfile.TemporaryDirectory() as tempdirname:
            tempdir = Path(tempdirname)
            font_zip.extractall(tempdir)
            fonts = []
            for suffix in ["ttc", "ttf", "otc", "otf"]:
                fonts += list(tempdir.rglob(f"*.{suffix}"))
            if LINUX:
                _install_fonts_linux(fonts)
            elif WINDOWS:
                _install_fonts_windows(fonts)


def _install_fonts_linux(fonts: List[Path]):
    """Install a list of fonts on Linux."""
    # Move all fonts to "~/.fonts".
    fontdir = Path("~/.local/share/fonts").expanduser()
    fontdir.mkdir(exist_ok=True)
    for font in fonts:
        shutil.copy(font, fontdir)
    run_command("fc-cache -f", "Refreshing font cache.", dry)
    print(f"{len(fonts)} fonts installed.")


def _install_fonts_windows(fonts: List[Path]):
    """Install a list of fonts on Windows."""
    fontdir = Path("~/Desktop/FONTS_TO_INSTALL").expanduser()
    for font in fonts:
        shutil.copy(font, fontdir)
    print(f"{len(fonts)} fonts copied to desktop.")
    print(red("You should install the fonts manually."))


if __name__ == "__main__":
    # Parse arguments.
    import argparse

    parser = argparse.ArgumentParser(
        description="Installation script for Unix dotfiles."
    )
    parser.add_argument("--dry", action="store_true", help="perform a dry run")
    parser.add_argument(
        "--complete",
        action="store_true",
        help="perform a complete run: also install fonts",
    )
    args = parser.parse_args()
    dry = args.dry
    complete = args.complete

    # Make sure the script is run in the correct directory.
    try:
        setup_directory()
    except DirectoryError:
        print("The script cannot find the correct directory to run.")
        sys.exit(1)

    # Install dot files.
    if WINDOWS:
        copy("./apps/git/dot_gitconfig", "~/.gitconfig", dry)
        copy(
            "./shell/PowerShell/Microsoft.PowerShell_profile.ps1",
            "~/Documents/WindowsPowerShell/Microsoft.PowerShell_profile.ps1",
            dry,
        )
        copy("./apps/rime", "%appdata%/rime", dry)
        windows_configure_cangjie6(dry)
        ahk_compile("./AutoHotkey", dry)
    if LINUX:
        copy("./shell/bash/bashrc", "~/.bashrc", dry)
        copy("./shell/bash/bash_profile", "~/.bash_profile", dry)
        copy("./apps/fontconfig/fonts.conf", "~/.config/fontconfig/fonts.conf", dry)
        if WSL:
            # Currently I use Nix and home-manager inside a Ubuntu WSL.
            copy("./apps/nix/home-manager/home.nix", "~/.config/home-manager/home.nix", dry)
        else:
            # These are for Linux without Nix, which I seldom use now. Changes
            # could be made if I end up using a native Linux some day.
            copy("./apps/fcitx5", "~/.config/fcitx5", dry)
            copy("./apps/rime", "~/.local/share/fcitx5/rime", dry)
            linux_configure_rime(dry)
            copy("./apps/xremap", "~/.config/xremap", dry)
            copy("./apps/git/dot_gitconfig", "~/.gitconfig", dry)
            if shutil.which("git-credential-manager"):
                run_command(
                    "git-credential-manager configure",
                    "Configuring git-credential-manager.",
                    dry,
                )

    # Load dconf.
    if LINUX and shutil.which("dconf") and not WSL:
        dconf_load("./apps/gnome_dconf/wm.dconf", "/org/gnome/desktop/wm/", dry)
        dconf_load("./apps/gnome_dconf/mutter.dconf", "/org/gnome/mutter/", dry)
        dconf_load(
            "./apps/gnome_dconf/media-keys.dconf",
            "/org/gnome/settings-daemon/plugins/media-keys/",
            dry,
        )
        dconf_load(
            "./apps/gnome_dconf/dash-to-panel.dconf",
            "/org/gnome/shell/extensions/dash-to-panel/",
            dry,
        )
        dconf_load(
            "./apps/gnome_dconf/improved-workspace-indicator.dconf",
            "/org/gnome/shell/extensions/improved-workspace-indicator/",
            dry,
        )
        dconf_load(
            "./apps/gnome_dconf/media-keys.dconf",
            "/org/gnome/shell/extensions/mediacontrols/",
            dry,
        )
    else:
        print("Skipping dconf configuration.")

    # Additional steps for a complete run.
    if complete:
        install_fonts(dry)
