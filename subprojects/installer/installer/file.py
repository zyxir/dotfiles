"""Utility for file operations."""

import logging
import os
import shutil
from pathlib import Path

from installer.job import Job
from installer.opt import Options
from installer.path import to_paths
from installer.style import emph_path


def copy(src: str, dst: str, opt: Options) -> None:
    """Copy `src` to `dst`, handling errors."""
    msg = f"Copying {emph_path(src)} to {emph_path(dst)}"

    def action() -> None:
        src_path, dst_path = to_paths(src, dst)
        prepare_paths(src_path, dst_path, opt)
        copy_path(src_path, dst_path, opt)
        
    Job(msg, action).run()


def link(src: str, dst: str, opt: Options) -> None:
    """Link to `src` as `dst`, handling errors.

    If `src` is a directory, create a directory of symbolic links, instead of a
    single symbolic link.
    """
    msg = f"Linking to {emph_path(src)} as {emph_path(dst)}"

    def action() -> None:
        src_path, dst_path = to_paths(src, dst)
        prepare_paths(src_path, dst_path, opt)
        link_path(src_path, dst_path, opt)
        
    Job(msg, action).run()


def prepare_paths(src_path: Path, dst_path: Path, opt: Options) -> None:
    """Prepare paths for a copying/linking operation."""
    # Make sure that the source exists.
    if not src_path.exists():
        raise FileExistsError(f"{emph_path(src_path)} does not exist")

    # If the destination directory does not exist, create directories.
    if not dst_path.parent.exists() and not opt.dry:
        os.makedirs(dst_path.parent)


def copy_path(src_path: Path, dst_path: Path, opt: Options) -> None:
    """Copy `src_path` to `dst_path`."""
    if opt.dry:
        return

    # Copy recursively while copying permissions and times.
    copy_recursively(src_path, dst_path)


def link_path(src_path: Path, dst_path: Path, opt: Options) -> None:
    """Link to `src_path` as `dst_path`.

    Fall back to copying if permission is insufficient.
    """
    if opt.dry:
        return

    try:
        # Try to create symbolic link(s).
        link_recursively(src_path, dst_path)
        
    except OSError:
        # Fall back to copying.
        copy_recursively(src_path, dst_path)


def copy_recursively(src_path: Path, dst_path: Path) -> None:
    """Recursively copy `src_path` to `dst_path`."""
    if src_path.is_dir():
        # This also creates any missing directories.
        shutil.copytree(src_path, dst_path, copy_function=shutil.copy2)
    else:
        shutil.copy2(src_path, dst_path)


def link_recursively(src_path: Path, dst_path: Path) -> None:
    """File-wise linking.

    If `src_path` is a file, make `dst_path` its symbolic link. Otherwise create
    a directory as `dst_path` and create symbolic links of files in `src_path`
    inside it.
    """
    if src_path.is_file():
        # Skip if destination is already the correct symlink.
        if dst_path.is_symlink() and dst_path.resolve().samefile(src_path):
            logging.debug(f"{emph_path(dst_path)} is already the correct symlink")
            return
        # Remove destination if it exists.
        if dst_path.exists():
            dst_path.unlink()
        # Create the symbolic link.
        os.symlink(src_path, dst_path, target_is_directory=False)
    else:
        # Make destination directory if it does not exist.
        if not dst_path.exists():
            os.makedirs(dst_path)
        # Link everything in the source.
        for entry in src_path.iterdir():
            entry_dst = dst_path.joinpath(entry.name)
            link_recursively(entry, entry_dst)
