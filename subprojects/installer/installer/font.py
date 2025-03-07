"""Utility for installing fonts."""

import os
import shutil
import zipfile
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import List

from installer.cmd import run_cmd
from installer.job import Job
from installer.opt import Options
from installer.os import IS_LINUX, IS_WINDOWS
from installer.path import some_path
from installer.style import emph_path


def install_zyfonts(opt: Options) -> None:
    """Install all fonts in "ZyFonts.zip", handling errors."""
    msg = "Installing fonts in {}".format(emph_path("ZyFonts.zip"))

    def action() -> None:
        tempdir = TemporaryDirectory()
        tempdir_path = Path(tempdir.name)
        extracted = extract_zyfonts(tempdir_path)
        install_fonts_in(extracted, opt)

    Job(msg, action).run()
    fontdir = Path.home().joinpath("Downloads/fonts_extracted")
    print("You should manually install fonts in {}".format(emph_path(fontdir)))


def extract_zyfonts(tempdir: Path) -> Path:
    """Extract "ZyFonts.zip", preferably to `tempdir`.

    If there is already an extracted "ZyFonts" directory, use that instead.

    Return the directory.
    """
    # Maybe there is already an unzipped "ZyFonts" directory.
    zyfonts_unzipped = some_path(
        "~/Downloads/ZyFonts",
        "/mnt/c/Users/zyxir/Downloads/ZyFonts",
    )

    # If not, find the zip archive and unzip it to a temp dir.
    if zyfonts_unzipped is None:
        zyfonts = some_path(
            "~/Downloads/ZyFonts.zip",
            "~/Zyspace/pcsetup/ZyFonts.zip",
            "/mnt/c/Users/zyxir/Downloads/ZyFonts.zip",
            "/mnt/c/Users/zyxir/Zyspace/pcsetup/ZyFonts.zip",
        )
        if zyfonts is None:
            raise Exception("Cannot find ZyFonts.zip")
        zyfonts_unzipped = tempdir.joinpath("ZyFonts")
        zyfonts_zip = zipfile.ZipFile(zyfonts, "r")
        zyfonts_zip.extractall(zyfonts_unzipped)

    # Return the unzipped ZyFonts directory.
    return zyfonts_unzipped


def install_fonts_in(dir: Path, opt: Options) -> None:
    """Install every font in `dir`."""
    # Collect all font paths.
    fonts = []
    exts = ["ttc", "ttf", "otc", "otf"]
    for ext in exts:
        fonts += dir.rglob(f"*.{ext}")

    # Install them in a platform-dependent way.
    if IS_LINUX:
        linux_install_fonts(fonts, opt)
    elif IS_WINDOWS:
        win_install_fonts(fonts, opt)
    else:
        raise OSError("Unsupported system.")


def linux_install_fonts(fonts: List[Path], opt: Options) -> None:
    """Install every font in `fonts` on Linux."""
    if opt.dry:
        return
    fontdir = Path("~/.local/share/fonts").expanduser()
    os.makedirs(fontdir, exist_ok=True)
    for font in fonts:
        font_dst = fontdir.joinpath(font.name)
        copy_font(font, font_dst)
    run_cmd("fc-cache -f", opt)


def win_install_fonts(fonts: List[Path], opt: Options) -> None:
    """Install every font in `fonts` on Windows."""
    if opt.dry:
        return
    fontdir = Path.home().joinpath("Downloads/fonts_extracted")
    fontdir.mkdir(exist_ok=True)
    for font in fonts:
        font_dst = fontdir.joinpath(font.name)
        copy_font(font, font_dst)


def copy_font(font: Path, font_dst: Path) -> None:
    """Copy `font` to `dst`.

    If `dst` already exists, don't copy at all, since copying a font may be
    heavy work.
    """
    if not font_dst.is_file():
        shutil.copy2(font,  font_dst)
