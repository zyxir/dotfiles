# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Installation

Run the installation script from the repo root:

```sh
python3 install.py          # normal run
python3 install.py --debug  # verbose output
```

The script symlinks config files on macOS and copies them on Windows. macOS installs: Git, Kitty, Rime, Zsh. Windows installs: Git, Rime, PowerShell.

**Rime prerequisite (macOS):** The schemas `cangjie5.schema.yaml` and `quick5.schema.yaml` must already exist in `~/Library/Rime/` before running the installer, or the Rime task will fail.

## Architecture

Config files live under `apps/<app>/` and are installed to their canonical locations by `install.py`:

| App | Source | Target (macOS) |
|-----|--------|----------------|
| Git | `apps/git/gitconfig` | `~/.gitconfig` |
| Kitty | `apps/kitty/` | `~/.config/kitty/` |
| Rime | `apps/rime/` | `~/Library/Rime/` |
| Zsh | `apps/zsh/{zshenv,zshrc,p10k.zsh}` | `~/{.zshenv,.zshrc,.p10k.zsh}` |
| PowerShell | `apps/PowerShell/Microsoft.PowerShell_profile.ps1` | `~/Documents/WindowsPowerShell/` |

`install.py` uses an abstract `Task` class — each app has a subclass that calls `link()`. To add support for a new app, add a `Task` subclass and append it to the appropriate platform's task list in `__main__`.

`link()` dispatches to `link_rec()` (symlinks, Unix) or `copy_rec()` (file copy, Windows). `copy_rec` only overwrites if the source is newer than the destination.

## Key Configuration Details

- **Zsh**: Uses Antigen (auto-downloaded to `~/.antigen/`) with Powerlevel10k theme. Proxy is set to `http://127.0.0.1:7897` when that port is reachable.
- **Rime**: Uses Cangjie5 and Quick5 input schemas. Platform-specific UI config in `squirrel.custom.yaml` (macOS) and `weasel.custom.yaml` (Windows).
- **scripts/disable-ctrl-space.reg**: Windows registry patch to free up Ctrl+Space for Rime.
