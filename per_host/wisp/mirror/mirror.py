#!/usr/bin/python3
"""Download files into srv/ for mirroring.  Run periodically via cron.

Each run overwrites existing files — the mirror always holds the latest
version.  Add new categories and URLs below as needed.
"""

import urllib.request
from pathlib import Path

CATEGORIES: dict[str, list[tuple[str, str]]] = {
    "fonts": [
        (
            "JetBrainsMono.zip",
            "https://github.com/ryanoasis/nerd-fonts/releases/latest/download/JetBrainsMono.zip",
        ),
        (
            "09_SourceHanSansSC.zip",
            "https://github.com/adobe-fonts/source-han-sans/releases/download/2.005R/09_SourceHanSansSC.zip",
        ),
    ],
}

SRV_DIR = Path(__file__).resolve().parent / "srv"

# Read domain from parent .env for printing access URLs
DOTENV = SRV_DIR.parent.parent / ".env"
DOMAIN = None
if DOTENV.is_file():
    for line in DOTENV.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line.startswith("DOMAIN="):
            DOMAIN = line.split("=", 1)[1].strip().strip('"').strip("'")


def main() -> None:
    for category, files in CATEGORIES.items():
        cat_dir = SRV_DIR / category
        cat_dir.mkdir(parents=True, exist_ok=True)
        for filename, url in files:
            dest = cat_dir / filename
            print(f"Downloading {filename}...")
            urllib.request.urlretrieve(url, dest)
            size = dest.stat().st_size / 1024 / 1024
            print(f"  → {dest} ({size:.1f} MB)")

    if DOMAIN:
        print(f"  https://mirror.{DOMAIN}/")


if __name__ == "__main__":
    main()
