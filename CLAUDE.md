# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Behavioral Guidelines

Guidelines to reduce common LLM coding mistakes. Merge with project-specific instructions as needed.

**Tradeoff:** These guidelines bias toward caution over speed. For trivial tasks, use judgment.

### 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them - don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

### 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

### 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it - don't delete it.

When your changes create orphans:
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

### 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:
- "Add validation" -> "Write tests for invalid inputs, then make them pass"
- "Fix the bug" -> "Write a test that reproduces it, then make it pass"
- "Refactor X" -> "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:
```
1. [Step] -> verify: [check]
2. [Step] -> verify: [check]
3. [Step] -> verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

---

**These guidelines are working if:** fewer unnecessary changes in diffs, fewer rewrites due to overcomplication, and clarifying questions come before implementation rather than after mistakes.

## Installation

Run the installation script from the repo root:

```sh
python3 install.py          # normal run
python3 install.py --debug  # verbose output
```

The script symlinks config files on macOS and copies them on Windows. macOS installs: Git, Ghostty, Kitty, Rime, Zsh, VSCodium. Windows installs: Git, Rime, PowerShell, VSCodium.

On macOS, the Rime task uses plum (`~/Library/Rime/plum/`) to install schemas (rime-ice, cangjie5, quick5) if their sentinel files are missing.

## Secrets

Secrets should be added to a local `~/.zshenv.secrets` file that is not tracked in git:

1. Create the file: `touch ~/.zshenv.secrets`
2. Edit it and add your tokens:
   ```sh
   export ANTHROPIC_AUTH_TOKEN="sk-..."
   ```
   Other environment variables (e.g., `ANTHROPIC_BASE_URL`, `ANTHROPIC_MODEL`) can also be set here if you prefer them outside of `settings.json`.
3. Reload your shell: `source ~/.zshrc`

The installer will warn you if this file is missing.

## Architecture

Config files live under `apps/<app>/` and are installed to their canonical locations by `install.py`:

| App | Source | Target (macOS) | Target (Windows) |
|-----|--------|----------------|------------------|
| Git | `apps/git/gitconfig` | `~/.gitconfig` | `~/.gitconfig` |
| Ghostty | `apps/ghostty/` | `~/.config/ghostty/` | — |
| Kitty | `apps/kitty/` | `~/.config/kitty/` | — |
| Rime | `apps/rime/` | `~/Library/Rime/` | `~/Library/Rime/` |
| Zsh | `apps/zsh/{zshenv,zshrc,p10k.zsh}` | `~/{.zshenv,.zshrc,.p10k.zsh}` | — |
| PowerShell | `apps/PowerShell/Microsoft.PowerShell_profile.ps1` | — | `~/Documents/WindowsPowerShell/` |
| VSCodium | `apps/vscodium/settings.json` | `~/Library/Application Support/VSCodium/User` | `~/AppData/Roaming/VSCodium/User` |

Fonts are installed by dedicated `Task` subclasses rather than symlinked from the repo:

| Task | Method | Source |
|------|--------|--------|
| `MesloLGSFont` | `install_fonts()` (direct download) | Raw GitHub URLs |
| `SourceHanSansFont` | `install_fonts_from_zip()` (zip extraction) | GitHub release archive |

Both helpers use `_system_font_dir()` to resolve the platform-specific fonts directory (`~/Library/Fonts` on macOS, `~/AppData/Local/Microsoft/Windows/Fonts` on Windows). Only missing fonts are installed; existing files are skipped.

`install.py` uses an abstract `Task` class -- each app has a subclass that calls `link()`. To add support for a new app, add a `Task` subclass and append it to the appropriate platform's task list in `__main__`.

`link()` calls `link_rec()` to create symlinks. On Windows, symlinks require Developer Mode or Administrator privileges. If a destination already exists but points to the wrong source, it is removed before creating the new symlink.

## Key Configuration Details

- **Zsh**: Uses Antigen (auto-downloaded to `~/.antigen/`) with Powerlevel10k theme. Proxy is set to `http://127.0.0.1:7897` when that port is reachable.
- **Rime**: Uses rime-ice (double_pinyin), Cangjie5, and Quick5 input schemas, installed via plum. Platform-specific UI config in `squirrel.custom.yaml` (macOS) and `weasel.custom.yaml` (Windows).
- **scripts/disable-ctrl-space.reg**: Windows registry patch to free up Ctrl+Space for Rime.
- **VSCodium**: `apps/vscodium/extensions.txt` lists installed extensions. After adding/removing extensions in the editor, regenerate it with `codium --list-extensions > apps/vscodium/extensions.txt` and commit. The installer runs `codium --install-extension` for any missing ones.
