#!/usr/bin/python3
"""Download font zips into srv/ for mirroring. Run periodically via cron.

Each run overwrites existing files — the mirror always holds the latest
version served by GitHub.
"""

import urllib.request
from pathlib import Path

FONTS: list[tuple[str, str]] = [
    (
        "JetBrainsMono.zip",
        "https://github.com/ryanoasis/nerd-fonts/releases/latest/download/JetBrainsMono.zip",
    ),
    (
        "09_SourceHanSansSC.zip",
        "https://github.com/adobe-fonts/source-han-sans/releases/download/2.005R/09_SourceHanSansSC.zip",
    ),
]

SRV_DIR = Path(__file__).resolve().parent / "srv"


def main() -> None:
    SRV_DIR.mkdir(parents=True, exist_ok=True)
    for filename, url in FONTS:
        dest = SRV_DIR / filename
        print(f"Downloading {filename}...")
        urllib.request.urlretrieve(url, dest)
        size = dest.stat().st_size / 1024 / 1024
        print(f"  → {dest} ({size:.1f} MB)")


if __name__ == "__main__":
    main()
