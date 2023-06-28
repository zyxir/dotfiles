#!/bin/python3
"""Cross-platform installation script for my dotfiles."""

import os
import platform
import shlex
import shutil
import subprocess
import sys
from typing import Optional, Union
from pathlib import Path


def cyan(path: Union[str, Path]) -> str:
    """Wrap path in cyan ANSI escape codes."""
    return "\u001b[36m" + str(path) + "\u001b[0m"


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
    if platform.system() == "Windows":
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
        cmd = [
            "C:\\Program Files\\AutoHotkey\\Compiler\\Ahk2Exe.exe",
            "/in",
            str(src),
        ]
        subprocess.run(cmd)
        shutil.move(src_exe, startup_dir)


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
    if shutil.which("git-credential-manager"):
        run_command(
            "git-credential-manager configure",
            "Configuring git-credential-manager.",
            dry,
        )
    copy("./mypy", "~/.config/mypy", dry)
    if WINDOWS:
        copy(
            "./Microsoft.PowerShell_profile.ps1",
            "~/Documents/WindowsPowerShell/Microsoft.PowerShell_profile.ps1",
            dry,
        )
        copy("./rime", "%appdata%/rime", dry)
        windows_configure_cangjie6(dry)
        ahk_compile("./AutoHotkey", dry)
    if LINUX:
        copy("./dot_bashrc", "~/.bashrc", dry)
        copy("./dot_bash_profile", "~/.bash_profile", dry)
        copy("./fonts.conf", "~/.config/fontconfig/fonts.conf", dry)
        copy("./fcitx5", "~/.config/fcitx5", dry)
        copy("./rime", "~/.local/share/fcitx5/rime", dry)
        copy("./xremap", "~/.config/xremap", dry)

    # Load dconf.
    if LINUX and shutil.which("dconf") and not WSL:
        dconf_load("./gnome_dconf/wm.dconf", "/org/gnome/desktop/wm/", dry)
        dconf_load("./gnome_dconf/mutter.dconf", "/org/gnome/mutter/", dry)
        dconf_load(
            "./gnome_dconf/media-keys.dconf",
            "/org/gnome/settings-daemon/plugins/media-keys/",
            dry,
        )
        dconf_load(
            "./gnome_dconf/dash-to-panel.dconf",
            "/org/gnome/shell/extensions/dash-to-panel/",
            dry,
        )
        dconf_load(
            "./gnome_dconf/improved-workspace-indicator.dconf",
            "/org/gnome/shell/extensions/improved-workspace-indicator/",
            dry,
        )
        dconf_load(
            "./gnome_dconf/trayIconsReloaded.dconf",
            "/org/gnome/shell/extensions/trayIconsReloaded/",
            dry,
        )
    else:
        print("Skipping dconf configuration.")
