"""Utility for file operations."""

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
    """Link to `src` as `dst`, handling errors."""
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
    if src_path.is_dir():
        # This also creates any missing directories.
        shutil.copytree(src_path, dst_path)
    else:
        # `copytree` uses `copy2` for copying individual files.
        shutil.copy2(src_path, dst_path)


def link_path(src_path: Path, dst_path: Path, opt: Options) -> None:
    """Link to `src_path` as `dst_path`.

    Fall back to copying if permission is insufficient.
    """
    if opt.dry:
        return

    # If the destination is already the correct symlink, do nothing.
    if dst_path.is_symlink() and dst_path.resolve().samefile(src_path):
        return

    # Otherwise, remove any existing destination.
    if dst_path.exists():
        remove_path(dst_path)

    try:
        # Try to create the symbolic link.
        os.symlink(src_path, dst_path, target_is_directory=src_path.is_dir())
    except OSError:
        # Fall back to copying.
        copy_path(src_path, dst_path, opt)


def remove_path(path: Path) -> None:
    """Remove `path` in the proper way."""
    if path.is_symlink() or path.is_file():
        path.unlink()
    else:
        shutil.rmtree(path)
