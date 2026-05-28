# CLAUDE.md

Guidance for Claude Code when working in this repository.

## Principles

- **Think before coding.** State assumptions. Surface tradeoffs. Ask when unclear—don't guess silently.
- **Simplicity first.** No speculative features or premature abstractions. No error handling for impossible states. If it feels overcomplicated, it is.
- **Surgical changes.** Don't refactor adjacent code or "improve" unrelated style. Match existing conventions. Every changed line must trace to the user's request.
- **Define success criteria.** Turn requests into verifiable goals. State a brief plan for multi-step tasks.
- **Keep docs in sync.** Update README.md and CLAUDE.md after major changes (new apps, new platforms, architecture shifts).

## Installation

```sh
python3 install.py          # normal run
python3 install.py --debug  # verbose output
```

The script symlinks config files on macOS and copies them on Windows.
On macOS, the Rime task uses plum (`~/Library/Rime/plum/`) to install schemas (rime-ice, cangjie5, quick5) if missing.

## Secrets

Add secrets to an untracked local file:

```sh
touch ~/.zshenv.secrets
# Add tokens like: export ANTHROPIC_AUTH_TOKEN="sk-..."
source ~/.zshrc
```

The installer warns if this file is missing.

## Architecture

Config files live under `apps/<app>/` and are installed by `install.py`:

| App | Source | Target (macOS) | Target (Windows) |
|-----|--------|----------------|------------------|
| Git | `apps/git/gitconfig` | `~/.gitconfig` | `~/.gitconfig` |
| Ghostty | `apps/ghostty/` | `~/.config/ghostty/` | — |
| Kitty | `apps/kitty/` | `~/.config/kitty/` | — |
| Rime | `apps/rime/` | `~/Library/Rime/` | `~/AppData/Roaming/Rime/` |
| Vim | `apps/vim/vimrc` | `~/.vimrc` | `~/.vimrc` |
| Zsh | `apps/zsh/{zshenv,zshrc,p10k.zsh}` | `~/{.zshenv,.zshrc,.p10k.zsh}` | — |
| PowerShell | `apps/PowerShell/Microsoft.PowerShell_profile.ps1` | — | `~/Documents/WindowsPowerShell/` |
| VSCodium | `apps/vscodium/settings.json` | `~/Library/Application Support/VSCodium/User` | `~/AppData/Roaming/VSCodium/User` |

`install.py` uses an abstract `Task` class—each app has a subclass that calls `link()`. To add a new app, create a `Task` subclass and append it to the platform's task list in `__main__`.

`link()` delegates to `link_rec()` to create symlinks. On Windows, symlinks require Developer Mode or Administrator privileges. Wrong-target destinations are removed before linking.

Fonts are installed by `Task` subclasses (`MesloLGSFont`, `SourceHanSansFont`) rather than symlinked. Only missing fonts are installed.

## Key Configuration Details

- **Zsh**: Uses Antigen (auto-downloaded to `~/.antigen/`) with Powerlevel10k. Proxy is `http://127.0.0.1:7897` when reachable.
- **Rime**: Uses rime-ice (double_pinyin), Cangjie5, and Quick5, installed via plum. Platform UI config in `squirrel.custom.yaml` (macOS) and `weasel.custom.yaml` (Windows).
- **scripts/disable-ctrl-space.reg**: Windows registry patch to free up Ctrl+Space for Rime.
- **VSCodium**: `apps/vscodium/extensions.txt` lists extensions. Regenerate with `codium --list-extensions > apps/vscodium/extensions.txt` after changes. The installer installs missing ones.
