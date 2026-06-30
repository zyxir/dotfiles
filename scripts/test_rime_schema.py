#!/usr/bin/python3
"""Test schema download logic against a temp directory.

Usage: python3 test_rime_schema.py [--keep]

This exercises the exact same _install_schema_zip function used by install.py,
but targets a disposable temp directory instead of your real Rime directory.
"""

import shutil
import sys
import tempfile
from pathlib import Path

# Point import at the repo root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from install import _SCHEMA_SOURCES, _install_schema_zip, SKIPPED


def test() -> None:
    keep = "--keep" in sys.argv
    tmpdir = tempfile.mkdtemp()
    rime_dir = Path(tmpdir)
    if keep:
        print(f"Temp dir: {tmpdir}")

    try:
        for url, prefix, patterns, sentinel, name in _SCHEMA_SOURCES:
            label = name or url.split("/")[4]
            print(f"\n{'='*60}")
            print(f"Schema: {label}")
            print(f"Sentinel: {sentinel}")

            result = _install_schema_zip(url, prefix, patterns, sentinel, rime_dir)

            if isinstance(result, type(SKIPPED)):
                print("  => SKIPPED (sentinel already present)")
                continue

            # Count and list extracted files
            files = sorted(
                str(p.relative_to(rime_dir)) for p in rime_dir.rglob("*") if p.is_file()
            )
            print(f"  => DONE — {len(files)} files extracted:")
            for f in files:
                size = (rime_dir / f).stat().st_size
                print(f"       {f} ({size:,} bytes)")

        # Test idempotency — second pass should skip everything
        print(f"\n{'='*60}")
        print("Second pass (idempotency check):")
        for url, prefix, patterns, sentinel, name in _SCHEMA_SOURCES:
            label = name or url.split("/")[4]
            result = _install_schema_zip(url, prefix, patterns, sentinel, rime_dir)
            status = "SKIP" if isinstance(result, type(SKIPPED)) else "DOWNLOADED"
            print(f"  {label}: {status}")
    finally:
        if not keep:
            shutil.rmtree(tmpdir)


if __name__ == "__main__":
    test()
