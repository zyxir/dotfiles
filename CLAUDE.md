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

The script symlinks config files on macOS and copies them on Windows. macOS installs: Git, Kitty, Rime, Zsh, Claude Code, VSCodium. Windows installs: Git, Rime, PowerShell, Claude Code, VSCodium.

**Rime prerequisite (macOS):** The schemas `cangjie5.schema.yaml` and `quick5.schema.yaml` must already exist in `~/Library/Rime/` before running the installer, or the Rime task will fail.

## Secrets

Secrets should be added to a local `~/.zshenv.secrets` file that is not tracked in git:

1. Create the file: `touch ~/.zshenv.secrets`
2. Edit it and add your tokens (e.g., `export ANTHROPIC_AUTH_TOKEN="sk-..."`)
3. Reload your shell: `source ~/.zshrc`

The installer will warn you if this file is missing.

## Architecture

Config files live under `apps/<app>/` and are installed to their canonical locations by `install.py`:

| App | Source | Target (macOS) |
|-----|--------|----------------|
| Git | `apps/git/gitconfig` | `~/.gitconfig` |
| Kitty | `apps/kitty/` | `~/.config/kitty/` |
| Rime | `apps/rime/` | `~/Library/Rime/` |
| Zsh | `apps/zsh/{zshenv,zshrc,p10k.zsh}` | `~/{.zshenv,.zshrc,.p10k.zsh}` |
| PowerShell | `apps/PowerShell/Microsoft.PowerShell_profile.ps1` | `~/Documents/WindowsPowerShell/` |
| Claude Code | `apps/claude-code/settings.json` | `~/.claude/settings.json` |
| VSCodium | `apps/vscodium/settings.json` | `~/Library/Application Support/VSCodium/User/settings.json` |

`install.py` uses an abstract `Task` class -- each app has a subclass that calls `link()`. To add support for a new app, add a `Task` subclass and append it to the appropriate platform's task list in `__main__`.

`link()` dispatches to `link_rec()` (symlinks, Unix) or `copy_rec()` (file copy, Windows). `copy_rec` only overwrites if the source is newer than the destination.

## Key Configuration Details

- **Zsh**: Uses Antigen (auto-downloaded to `~/.antigen/`) with Powerlevel10k theme. Proxy is set to `http://127.0.0.1:7897` when that port is reachable.
- **Rime**: Uses Cangjie5 and Quick5 input schemas. Platform-specific UI config in `squirrel.custom.yaml` (macOS) and `weasel.custom.yaml` (Windows).
- **scripts/disable-ctrl-space.reg**: Windows registry patch to free up Ctrl+Space for Rime.
- **VSCodium**: `apps/vscodium/extensions.txt` lists installed extensions. After adding/removing extensions in the editor, regenerate it with `codium --list-extensions > apps/vscodium/extensions.txt` and commit. The installer runs `codium --install-extension` for any missing ones.
