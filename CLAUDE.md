# CLAUDE.md

Guidance for Claude Code when working in this repository.

## Principles

- **Think before coding.** State assumptions. Surface tradeoffs. Ask when unclear—don't guess silently.
- **Simplicity first.** No speculative features or premature abstractions. No error handling for impossible states. If it feels overcomplicated, it is.
- **Surgical changes.** Don't refactor adjacent code or "improve" unrelated style. Match existing conventions. Every changed line must trace to the user's request.
- **Define success criteria.** Turn requests into verifiable goals. State a brief plan for multi-step tasks.
- **Keep docs in sync.** Update README.md and CLAUDE.md after major changes (new apps, new platforms, architecture shifts).
- **Never auto-commit.** Always ask before committing. The user reviews every commit.
- **Accurate co-author.** Every commit must end with the exact line:
  `Co-Authored-By: <MODEL_NAME> <noreply@<VENDOR>.com>`
  where `<MODEL_NAME>` and `<VENDOR>` come from the "powered by" line in the system prompt (e.g., "powered by the model deepseek-v4-pro" → `DeepSeek V4 Pro <noreply@deepseek.com>`).

## Installation

```sh
python3 install.py                 # normal run
python3 install.py --debug         # verbose output
python3 install.py --proxy <URL>   # use specific proxy for downloads
python3 install.py --skip-sudo     # skip docker compose operations
```

The script symlinks config files on all platforms. On Windows, symlinks require Developer Mode or Administrator privileges.
On macOS, the Rime task uses plum (`~/Library/Rime/plum/`) to install schemas (rime-ice, cangjie5, quick5) if missing.

Proxy detection order: `--proxy` flag > `https_proxy`/`http_proxy` env vars > auto-probe `127.0.0.1:7897`. All network operations (font downloads, git clone, schema install, extension install) route through the configured proxy. The active proxy is displayed alongside environment and platform at startup.

## Architecture

Config files live under `per_app/<app>/` (cross-platform) or `per_host/<hostname>/` (machine-specific) and are installed by `install.py`:

### Per-app configs (`AppTask`)

| App | Source | Target (macOS) | Target (Windows) |
|-----|--------|----------------|------------------|
| Git | `per_app/git/gitconfig` | `~/.gitconfig` | `~/.gitconfig` |
| Ghostty | `per_app/ghostty/` | `~/.config/ghostty/` | — |
| Rime | `per_app/rime/` | `~/Library/Rime/` | `~/AppData/Roaming/Rime/` |
| Vim | `per_app/vim/vimrc` | `~/.vimrc` | `~/.vimrc` |
| Firefox | `per_app/firefox/user.js` | `<profile>/user.js` (auto-discovered) | — |
| Zsh | `per_app/zsh/{zshenv,zshrc,p10k.zsh}` | `~/{.zshenv,.zshrc,.p10k.zsh}` | — |
| PowerShell | `per_app/PowerShell/Microsoft.PowerShell_profile.ps1` | — | `~/Documents/WindowsPowerShell/` |
| VSCodium | `per_app/vscodium/settings.json` | `~/Library/Application Support/VSCodium/User` | `~/AppData/Roaming/VSCodium/User` |

### Per-host configs (`HostTask`)

Each subdirectory under `per_host/` is named after a machine's hostname.
The matching `VpsHost` task activates only when `socket.gethostname()` matches.

| Host | Source |
|------|--------|
| wisp | `per_host/wisp/{docker-compose.yml,Caddyfile,.env.example,mirror/,subconv/}` |

`install.py` uses two task types: `AppTask` (gated by `skip_envs`) and `HostTask` (gated by hostname match). To add a new app, subclass `AppTask` and append it to the platform's task list. To add a new host, create `per_host/<hostname>/` and the Linux task list auto-discovers it.

`VpsHost` expects `.env` at `per_host/<hostname>/.env`. Copy it to the VPS manually (e.g., `scp .env wisp:~/dotfiles/per_host/wisp/.env`). The file is gitignored.

`VpsHost` also expects `subconv/subconv.env` alongside `.env` and reads `CLOUDFLARE_API_TOKEN` from `.env` for automatic DNS record management (zone IDs are looked up via the API). When configured, the installer upserts A records on Cloudflare for every domain in the Caddyfile before starting Docker services.

`VpsHost` includes a Tailscale check step. If Tailscale is installed but not authenticated, it prints a hint to run `sudo tailscale up --ssh`. Auth is manual (OAuth via browser) — no secrets needed in `.env`.

### Bootstrap assets (`bootstrap/`)

Files for cold-starting a machine — referenced by setup docs, not used by `install.py` directly.

| Platform | Asset | Purpose |
|----------|-------|---------|
| macOS | `bootstrap/macos/Brewfile` | Minimal package list (`brew bundle install --file=...`) |
| Windows | `bootstrap/windows/winget-packages.json` | Minimal package list (`winget import -i ...`) |
| Windows | `bootstrap/windows/disable-ctrl-space.reg` | Disable Ctrl+Space IME shortcut (conflicts with editor hotkeys) |
| VPS | `bootstrap/vps/vps_bootstrap.sh` | Shared Vultr startup script for Debian 12 — installs Docker and Tailscale, hardens SSH (port 9906, key-only), configures UFW (including tailscale0 interface), fail2ban, unattended-upgrades. Paste into Vultr's "Startup Script" field when creating an instance. |

The Brewfile and winget JSON are minimal, audited lists — not a full dump of every installed package. They contain only what's essential on any machine.

### Task internals

`link()` delegates to `link_rec()` to create symlinks. Wrong-target destinations are removed before linking.

Fonts are installed by `AppTask` subclasses (`Fonts`) rather than symlinked. Only missing fonts are installed.

### Operational notes

- **VSCodium**: Regenerate `extensions.txt` with `codium --list-extensions > per_app/vscodium/extensions.txt` after installing or removing extensions.
- **scripts/test-doh.py**: Benchmarks DoH servers for reachability and latency. Tests domestic servers directly, foreign servers through the proxy at 7897. Re-run when changing DNS providers or if connectivity issues arise.
- **subconv (wisp)**: Subscription converter under `per_host/wisp/subconv/`. `subconv.py` reuses `Script.js` directly — reads it at runtime, appends a stdin/stdout CLI wrapper, runs it via `node`. Python handles YAML/HTTP; Script.js handles transform logic. Reads `subconv/subconv.env` for the subscription URL (separate from `.env` — changes more often). Outputs to `subconv/srv/<secret>/ZyProxy`, served as a static file by Caddy at `subconv.<domain>/<secret>/ZyProxy`. Run via cron every 30 min. Depends on `nodejs` and `python3-yaml` (installed by `bootstrap/vps/vps_bootstrap.sh`). `Script.js` can also be copied manually into Clash Verge Rev as a backup when the VPS is unavailable.

- **mirror (wisp)**: Download mirror under `per_host/wisp/mirror/`. `mirror.py` fetches files (e.g., font zips) from upstream sources into `mirror/srv/`, served by Caddy at `mirror.<domain>/`. Run via cron weekly (Sunday 3am). Add new download targets in `mirror.py` as needed.
