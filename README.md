# Dotfiles

Cross-platform dotfiles managed via a Python installer. Supports macOS and Windows.

## Installation

Requires Python 3.

```sh
python install.py          # normal run
python install.py --debug  # verbose output
```

Add secrets to an untracked local file:

```sh
touch ~/.zshenv.secrets
# Add tokens like: export ANTHROPIC_AUTH_TOKEN="sk-..."
```

## What's Configured

- [Git](https://git-scm.com) — distributed version control (macOS & Windows)
- [Ghostty](https://ghostty.org) — GPU-accelerated terminal emulator (macOS)
- [Rime](https://rime.im) — extensible input method engine (macOS & Windows)
- [Vim](https://www.vim.org) — text editor (macOS & Windows)
- [Zsh](https://www.zsh.org) — Unix shell with [Antigen](https://github.com/zsh-users/antigen) plugin manager and [Powerlevel10k](https://github.com/romkatv/powerlevel10k) prompt (macOS)
- [PowerShell](https://learn.microsoft.com/en-us/powershell/) — Windows shell (Windows)
- [VSCodium](https://vscodium.com) — open-source build of VS Code (macOS & Windows)

## Project Structure

- `per_app/` — cross-platform application configs.
- `per_host/` — machine-specific configs (matched by hostname).
- `scripts/` — utility scripts (e.g., Windows registry patches).
- `install.py` — cross-platform installation script.
