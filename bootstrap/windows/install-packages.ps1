# Minimal Windows packages — every entry is audited and intentional.
# Usage: powershell -ExecutionPolicy Bypass -File bootstrap/windows/install-packages.ps1
#
# winget install is idempotent: already-installed packages are skipped.
# Packages that are already winget-managed will be upgraded if a newer
# version is available unless --exact is pinned.

# --- Terminal & shell tools ---
winget install BurntSushi.ripgrep.MSVC
winget install sharkdp.fd
winget install Git.Git

# --- Editors ---
winget install Neovim.Neovim
winget install VSCodium.VSCodium

# --- Browsers ---
winget install Mozilla.Firefox
winget install Google.Chrome

# --- Python toolchain ---
winget install Python.Python.3.13
winget install Python.Launcher
winget install astral-sh.uv

# --- Input & knowledge ---
winget install Rime.Weasel
winget install Logseq.Logseq

# --- Windows essentials ---
winget install Microsoft.PowerToys --exact --version 0.95.0
winget install voidtools.Everything

# --- Connectivity ---
winget install tailscale.tailscale
