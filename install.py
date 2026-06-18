#!/usr/bin/python3
"""Cross-platform installation script for my dotfiles."""

from __future__ import annotations

import argparse
import configparser
import getpass
import json
import logging
import os
import platform
import re
import shutil
import socket
import ssl
import subprocess
import sys
import tempfile
import urllib.parse
import urllib.request
import zipfile
from abc import ABC, abstractmethod
from collections.abc import Callable
from pathlib import Path
from typing import Union


class _DebugTracker(logging.Handler):
    """Logging handler that records whether any debug message was emitted."""

    def __init__(self) -> None:
        super().__init__(logging.DEBUG)
        self.fired = False

    def reset(self) -> None:
        self.fired = False

    def emit(self, record: logging.LogRecord) -> None:
        self.fired = True


def setup_logging(debug: bool = False) -> _DebugTracker:
    """Set up logging. Returns a tracker that detects debug output."""
    tracker = _DebugTracker()
    logging.getLogger().addHandler(tracker)
    if debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logging.basicConfig(level=logging.DEBUG)
    return tracker


def pathify(s: Union[str, os.PathLike]) -> Path:
    """Convert `s` to an absolute `Path` object.

    Expand "~" (user home) and env vars in the process.
    """
    s = os.path.expandvars(s)
    path = Path(s).expanduser().absolute()
    return path


def already_linked(src: Path, dst: Path) -> bool:
    """Return True if `dst` points to `src`."""
    if dst.is_symlink():
        try:
            return dst.resolve().samefile(src)
        except Exception:
            return False
    return False


def link_rec(src: Path, dst: Path) -> bool:
    """Symlink `dst` to `src` recursively without checking. Returns True if any symlink was created."""
    if src.is_file():
        if already_linked(src, dst):
            logging.debug("skip existing '%s'", dst)
            return False
        elif dst.is_symlink() or dst.exists():
            logging.debug("remove incorrect '%s'", dst)
            dst.unlink()
        logging.debug("creating symlink '%s'", dst)
        try:
            dst.symlink_to(src)
        except OSError as e:
            if getattr(e, "winerror", None) == 1314:
                raise PermissionError(
                    "Cannot create symlinks. Either:\n"
                    "  • Enable Developer Mode: Settings → Privacy & Security → For Developers\n"
                    "  • Or re-run this script as Administrator"
                ) from e
            raise
        return True
    else:
        dst.mkdir(exist_ok=True)
        results = [link_rec(s, dst.joinpath(s.name)) for s in src.iterdir()]
        return any(results)


def cleanup_dead_symlinks(path: Path) -> None:
    """Remove all dead symlinks in a directory recursively."""
    if not path.is_dir():
        return
    for entry in path.rglob("*"):
        if entry.is_symlink() and not entry.exists():
            logging.debug("remove dead symlink '%s'", entry)
            entry.unlink()


def link(
    src: Union[str, os.PathLike], dst: Union[str, os.PathLike], mkdir: bool = False
) -> bool:
    """Symlink `dst` to `src`. Returns True if any symlink was created.

    On Windows, this requires Developer Mode or Administrator privileges.
    If `dst` is a directory, removes any dead symlinks after symlinking.
    """
    src_p, dst_p = pathify(src), pathify(dst)
    if not src_p.exists():
        raise FileNotFoundError(f"'{src_p}' does not exist")
    dst_p.parent.mkdir(parents=True, exist_ok=True)
    created = link_rec(src_p, dst_p)
    if src_p.is_dir():
        cleanup_dead_symlinks(dst_p)
    return created


class _Skipped:
    pass


SKIPPED = _Skipped()

# Global indentation — incremented by task/step nesting so hints
# align automatically without manual leading spaces.
indent = 0


def print_indented(msg: str, extra: int = 0) -> None:
    """Print *msg* with each line prefixed by indent+extra spaces."""
    prefix = " " * (indent + extra)
    for line in msg.splitlines() or [""]:
        print(f"{prefix}{line}", flush=True)


class Step:
    """A named sub-action within a task."""

    def __init__(self, description: str, fn: Callable[[], str | _Skipped | None]):
        self.description = description
        self._fn = fn

    def run(self) -> str | _Skipped | None:
        return self._fn()


class Task(ABC):
    """A task to perform."""

    @abstractmethod
    def steps(self) -> list[Step]:
        """Return the list of steps that make up this task."""


class AppTask(Task):
    """Task for per-app configuration.

    Uses `skip_envs` to opt out of specific environments.
    """

    skip_envs: set[str] = set()


class HostTask(Task):
    """Task for per-host configuration.

    Active only when the current machine's hostname matches the task's
    configured hostname.  No `skip_envs` — the hostname match is the
    sole gate.
    """

    def __init__(self, hostname: str):
        self.hostname = hostname

    @property
    def is_active(self) -> bool:
        return socket.gethostname() == self.hostname


class Git(AppTask):
    """Install git config."""

    skip_envs = {"corporate"}

    def steps(self) -> list[Step]:
        return [Step("Link ~/.gitconfig", self._run)]

    def _run(self) -> str | _Skipped | None:
        if not link("./per_app/git/gitconfig", "~/.gitconfig"):
            return SKIPPED


PLUM_URL = "https://github.com/rime/plum.git"
# (plum schema name, sentinel file installed by plum)
PLUM_SCHEMAS: list[tuple[list[str], str, str | None]] = [
    (["cangjie"], "cangjie5.schema.yaml", None),
    (["quick"], "quick5.schema.yaml", None),
    (
        [
            "iDvel/rime-ice:others/recipes/full",
            "iDvel/rime-ice:others/recipes/config:schema=double_pinyin",
        ],
        "rime_ice.schema.yaml",
        "rime-ice",
    ),
]


def _rime_dir() -> Path:
    """Return the platform-specific Rime user data directory."""
    if platform.system() == "Darwin":
        return pathify("~/Library/Rime")
    return pathify("~/AppData/Roaming/Rime")


class Rime(AppTask):
    """Install rime config."""

    skip_envs = {"vps"}

    def steps(self) -> list[Step]:
        return [
            Step("Clone plum into Rime directory", self._install_plum),
            *[
                Step(
                    f"Install schema: {name or pkgs[0]}",
                    self._schema_installer(pkgs, sentinel),
                )
                for pkgs, sentinel, name in PLUM_SCHEMAS
            ],
            Step("Link config", self._run),
        ]

    def _schema_installer(
        self, packages: list[str], sentinel: str
    ) -> Callable[[], str | _Skipped | None]:
        def _install() -> str | _Skipped | None:
            rime_dir = _rime_dir()
            if (rime_dir / sentinel).exists():
                return SKIPPED
            if platform.system() == "Windows":
                rime_install = rime_dir / "plum" / "rime-install.bat"
                shell = ["cmd", "/c", str(rime_install)]
            else:
                rime_install = rime_dir / "plum" / "rime-install"
                shell = ["bash", str(rime_install)]
            for pkg in packages:
                logging.debug("installing schema: %s", pkg)
                subprocess.run(
                    shell + [pkg],
                    check=True,
                    capture_output=True,
                    env={**os.environ, "rime_dir": str(rime_dir)},
                )

        return _install

    def _install_plum(self) -> str | _Skipped | None:
        dst = _rime_dir() / "plum"
        if dst.exists():
            return SKIPPED
        logging.debug("cloning plum into %s", dst)
        cmd = ["git", "clone", "--depth", "1"]
        proxy = _proxy_url()
        if proxy:
            cmd += ["-c", f"http.proxy={proxy}", "-c", f"https.proxy={proxy}"]
        cmd += [PLUM_URL, str(dst)]
        subprocess.run(cmd, check=True, capture_output=True)

    def _run(self) -> str | _Skipped | None:
        rime_dir = _rime_dir()
        created = link("./per_app/rime", rime_dir)
        if not created:
            return SKIPPED


class Zsh(AppTask):
    """Install zsh config."""

    skip_envs = {"vps"}

    def steps(self) -> list[Step]:
        return [Step("Link config files", self._run)]

    def _run(self) -> str | _Skipped | None:
        a = link("./per_app/zsh/zshenv", "~/.zshenv")
        b = link("./per_app/zsh/zshrc", "~/.zshrc")
        c = link("./per_app/zsh/p10k.zsh", "~/.p10k.zsh")
        if not os.environ.get("SHELL", "").endswith("zsh"):
            return "❗Consider setting zsh as your default shell."
        if not (a or b or c):
            return SKIPPED


class PowerShell(AppTask):
    """Install PowerShell config."""

    def steps(self) -> list[Step]:
        return [Step("Link profile", self._run)]

    def _run(self) -> str | _Skipped | None:
        if not link(
            "./per_app/PowerShell/Microsoft.PowerShell_profile.ps1",
            "~/Documents/WindowsPowerShell/Microsoft.PowerShell_profile.ps1",
        ):
            return SKIPPED


def _system_font_dir() -> Path:
    """Return the platform-specific system fonts directory."""
    if platform.system() == "Darwin":
        return pathify("~/Library/Fonts")
    return pathify("~/AppData/Local/Microsoft/Windows/Fonts")


MIRROR = "mirror.ericzhuochen.com"
USER_AGENT = "Mozilla/5.0"


def _mirror_url(path: str) -> str:
    """Return the full URL for *path* on the download mirror."""
    return f"https://{MIRROR}/{path.lstrip('/')}"


def install_fonts_from_zip(
    url: str, filenames: list[str] | None = None, fallback: str | None = None
) -> list[str]:
    """Download and extract missing fonts from a zip archive.

    Tries *url* first.  If it fails and *fallback* is provided, retries
    with the fallback URL.

    Returns the list of filenames that were actually installed.
    """
    font_dir = _system_font_dir()
    font_dir.mkdir(parents=True, exist_ok=True)

    if filenames is not None and all((font_dir / f).exists() for f in filenames):
        logging.debug("all fonts already installed, skipping download")
        return []

    def _download(src: str, dest: str, verify_ssl: bool = True) -> None:
        logging.debug("downloading %s", src)
        req = urllib.request.Request(src, headers={"User-Agent": USER_AGENT})
        if verify_ssl:
            urllib.request.urlretrieve(req, dest)
        else:
            # Corporate proxies often perform SSL inspection — retry
            # without certificate verification so the download can
            # still go through the proxy.
            ctx = ssl._create_unverified_context()
            https_handler = urllib.request.HTTPSHandler(context=ctx)
            proxy_handler = urllib.request.ProxyHandler()
            handler = urllib.request.build_opener(https_handler, proxy_handler)
            with handler.open(req) as resp, open(dest, "wb") as f:
                shutil.copyfileobj(resp, f)

    with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp:
        try:
            _download(url, tmp.name)
        except Exception:
            try:
                _download(url, tmp.name, verify_ssl=False)
            except Exception:
                if fallback:
                    logging.debug("mirror failed, trying fallback: %s", fallback)
                    try:
                        _download(fallback, tmp.name)
                    except Exception:
                        _download(fallback, tmp.name, verify_ssl=False)
                else:
                    raise
        tmp_path = Path(tmp.name)

    try:
        with tempfile.TemporaryDirectory() as extract_dir:
            with zipfile.ZipFile(tmp_path, "r") as zf:
                zf.extractall(extract_dir)

            installed: list[str] = []
            for ext in ("*.otf", "*.ttf"):
                for src in Path(extract_dir).rglob(ext):
                    if filenames is not None and src.name not in filenames:
                        continue
                    dst = font_dir / src.name
                    if dst.exists():
                        logging.debug("font already installed: %s", src.name)
                        continue
                    logging.debug("installing font: %s", src.name)
                    shutil.copy2(src, dst)
                    installed.append(src.name)
    finally:
        tmp_path.unlink()

    return installed


class Fonts(AppTask):
    """Install fonts."""

    skip_envs = {"vps"}

    def steps(self) -> list[Step]:
        return [
            Step("JetBrainsMono Nerd Font", self._jetbrains_mono),
            Step("Source Han Sans", self._source_han_sans),
        ]

    def _jetbrains_mono(self) -> str | _Skipped | None:
        upstream = "https://github.com/ryanoasis/nerd-fonts/releases/latest/download/JetBrainsMono.zip"
        installed = install_fonts_from_zip(
            _mirror_url("fonts/JetBrainsMono.zip"),
            [
                "JetBrainsMonoNerdFontMono-Regular.ttf",
                "JetBrainsMonoNerdFontMono-Bold.ttf",
                "JetBrainsMonoNerdFontMono-Italic.ttf",
                "JetBrainsMonoNerdFontMono-BoldItalic.ttf",
            ],
            fallback=upstream,
        )
        if not installed:
            return SKIPPED
        return f"Installed {len(installed)} file(s): {', '.join(installed)}."

    def _source_han_sans(self) -> str | _Skipped | None:
        upstream = (
            "https://github.com/adobe-fonts/source-han-sans/"
            "releases/download/2.005R/09_SourceHanSansSC.zip"
        )
        installed = install_fonts_from_zip(
            _mirror_url("fonts/09_SourceHanSansSC.zip"),
            [
                "SourceHanSansSC-ExtraLight.otf",
                "SourceHanSansSC-Light.otf",
                "SourceHanSansSC-Normal.otf",
                "SourceHanSansSC-Regular.otf",
                "SourceHanSansSC-Medium.otf",
                "SourceHanSansSC-Bold.otf",
                "SourceHanSansSC-Heavy.otf",
            ],
            fallback=upstream,
        )
        if not installed:
            return SKIPPED
        return f"Installed {len(installed)} file(s): {', '.join(installed)}."


class Vim(AppTask):
    """Install vim config."""

    def steps(self) -> list[Step]:
        return [Step("Link ~/.vimrc", self._run)]

    def _run(self) -> str | _Skipped | None:
        if not link("./per_app/vim/vimrc", "~/.vimrc"):
            return SKIPPED


class Ghostty(AppTask):
    """Install Ghostty config."""

    skip_envs = {"vps"}

    def steps(self) -> list[Step]:
        return [Step("Link ~/.config/ghostty", self._run)]

    def _run(self) -> str | _Skipped | None:
        if not link("./per_app/ghostty", "~/.config/ghostty"):
            return SKIPPED


class Firefox(AppTask):
    """Install Firefox user.js."""

    skip_envs = {"corporate"}

    def steps(self) -> list[Step]:
        return [Step("Link user.js into profile", self._run)]

    def _find_profile_dir(self) -> Path | None:
        """Parse profiles.ini and return the active profile directory."""
        if platform.system() == "Darwin":
            firefox_dir = pathify("~/Library/Application Support/Firefox")
        elif platform.system() == "Windows":
            firefox_dir = pathify("~/AppData/Roaming/Mozilla/Firefox")
        else:
            firefox_dir = pathify("~/.mozilla/firefox")

        ini_path = firefox_dir / "profiles.ini"
        if not ini_path.exists():
            return None

        config = configparser.ConfigParser()
        config.read(ini_path)

        # 1) Look for [Install*] with Locked=1 (most reliable)
        for section in config.sections():
            if section.startswith("Install") and config[section].get("locked") == "1":
                return firefox_dir / config[section].get("default", "")

        # 2) StartWithLastProfile=0 points to a specific profile index
        last = config.get("General", "startwithlastprofile", fallback="1")
        profile_section = f"Profile{last}"
        if config.has_section(profile_section):
            return firefox_dir / config[profile_section].get("path", "")

        # 3) Fall back to the first profile marked Default=1
        for section in config.sections():
            if section.startswith("Profile") and config[section].get("default") == "1":
                return firefox_dir / config[section].get("path", "")

        return None

    def _run(self) -> str | _Skipped | None:
        profile_dir = self._find_profile_dir()
        if profile_dir is None:
            return "❗Could not find Firefox profile. Create one and re-run."
        if not link("./per_app/firefox/user.js", f"{profile_dir}/user.js"):
            return SKIPPED


class VSCodium(AppTask):
    """Install VSCodium config and extensions."""

    skip_envs = {"vps", "corporate"}

    def steps(self) -> list[Step]:
        return [
            Step("Link settings.json", self._link_settings),
            Step("Install extensions", self._install_extensions),
        ]

    def _link_settings(self) -> str | _Skipped | None:
        if platform.system() == "Darwin":
            user_dir = "~/Library/Application Support/VSCodium/User"
        else:
            user_dir = "~/AppData/Roaming/VSCodium/User"
        if not link("./per_app/vscodium/settings.json", f"{user_dir}/settings.json"):
            return SKIPPED

    def _install_extensions(self) -> str | _Skipped | None:
        codium = shutil.which("codium")
        if codium is None:
            return "❗Install VSCodium to sync extensions (codium CLI not found)."

        extensions_file = pathify("./per_app/vscodium/extensions.txt")
        wanted = [
            line.strip()
            for line in extensions_file.read_text().splitlines()
            if line.strip() and not line.startswith("#")
        ]
        installed = set(
            subprocess.run(
                [codium, "--list-extensions"],
                capture_output=True,
                text=True,
                check=True,
            ).stdout.split()
        )
        missing = [ext for ext in wanted if ext not in installed]
        if not missing:
            return SKIPPED
        for ext in missing:
            logging.debug("installing extension %s", ext)
            subprocess.run(
                [codium, "--install-extension", ext, "--force"],
                capture_output=True,
                check=True,
            )
        if missing:
            return (
                f"Installed {len(missing)} VSCodium extension(s): {', '.join(missing)}"
            )


class PowerToys(AppTask):
    """Install PowerToys config."""

    skip_envs = {"vps", "corporate"}

    def steps(self) -> list[Step]:
        return [Step("Link config", self._run)]

    def _run(self) -> str | _Skipped | None:
        if not link(
            "./per_app/powertoys",
            "~/AppData/Local/Microsoft/PowerToys",
        ):
            return SKIPPED


class VpsHost(HostTask):
    """VPS host config (per_host/<hostname>/)."""

    def __init__(self, hostname: str, skip_sudo: bool = False):
        super().__init__(hostname)
        self.skip_sudo = skip_sudo

    def steps(self) -> list[Step]:
        return [
            Step("Check for .env files", self._check_env),
            Step("Configure DNS records", self._configure_dns),
            Step("Start Docker services", self._docker_up),
            Step("Setup cron jobs", self._setup_crons),
            Step("Check Tailscale", self._tailscale_check),
        ]

    @property
    def _host_dir(self) -> Path:
        return Path(f"./per_host/{self.hostname}")

    def _check_env(self) -> str | _Skipped | None:
        host_dir = self._host_dir
        if not host_dir.is_dir():
            return f"❗No config directory for host '{self.hostname}'."
        if not (host_dir / "docker-compose.yml").exists():
            return "❗No docker-compose.yml found."

        missing = []
        for name in (".env", "subconv/subconv.env"):
            if not (host_dir / name).exists():
                example = f"{name}.example"
                missing.append(f"  {name} (copy from {example})")

        if not missing:
            return SKIPPED

        return "❗Missing env files:\n" + "\n".join(missing)

    # ----- DNS helpers -------------------------------------------------

    @staticmethod
    def _read_env(host_dir: Path) -> dict[str, str]:
        """Parse KEY=VALUE from a .env file (no shell expansion)."""
        env_file = host_dir / ".env"
        if not env_file.is_file():
            return {}
        result: dict[str, str] = {}
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, _, value = line.partition("=")
                result[key.strip()] = value.strip().strip("\"'")
        return result

    @staticmethod
    def _parse_caddyfile(host_dir: Path, env: dict[str, str]) -> list[str]:
        """Extract domain names from Caddyfile blocks, resolving {$VAR} placeholders."""
        caddyfile = host_dir / "Caddyfile"
        if not caddyfile.is_file():
            return []

        domains: list[str] = []
        for line in caddyfile.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            m = re.match(r"^(\S+)\s*\{", line)
            if m:
                domain = m.group(1)
                # Resolve {$VAR:default} placeholders
                domain = re.sub(
                    r"\{\$(\w+)(?::(\S+))?\}",
                    lambda m: env.get(m.group(1), m.group(2) or m.group(0)),
                    domain,
                )
                domains.append(domain)
        return domains

    @staticmethod
    def _cf_zone_id(token: str, domain: str, cache: dict[str, str]) -> str | None:
        """Look up the Cloudflare Zone ID for a domain's root zone.

        The root zone is the last two labels of the domain (e.g.,
        ``example.com`` from ``sub.example.com``).  Results are cached
        so subdomains of the same zone don't repeat the lookup.
        """
        parts = domain.rsplit(".", 2)
        root = ".".join(parts[-2:]) if len(parts) >= 2 else domain

        if root in cache:
            return cache[root]

        url = f"https://api.cloudflare.com/client/v4/zones?name={urllib.parse.quote(root, safe='')}"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        req = urllib.request.Request(url, headers=headers, method="GET")
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read())
        except OSError:
            return None

        if data.get("success") and data.get("result"):
            zone_id = data["result"][0]["id"]
            cache[root] = zone_id
            return zone_id
        return None

    @staticmethod
    def _cf_api(
        token: str, zone_id: str, method: str, path: str, body: dict | None = None
    ) -> dict:
        """Call Cloudflare API. Raises on HTTP / network errors."""
        url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/{path}"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        data = json.dumps(body).encode() if body else None
        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read())

    def _configure_dns(self) -> str | _Skipped | None:
        """Upsert A records on Cloudflare for every domain in the Caddyfile.

        Requires CLOUDFLARE_API_TOKEN in .env.  Zone IDs are looked up via
        the API (the token needs Zone.Zone read + Zone.DNS edit).
        Skipped silently when the token is absent.
        """
        env = self._read_env(self._host_dir)

        token = env.get("CLOUDFLARE_API_TOKEN")
        if not token:
            return SKIPPED

        domains = self._parse_caddyfile(self._host_dir, env)
        if not domains:
            return "⚠ No domain blocks found in Caddyfile."

        # Discover public IP (this runs on the VPS, so it IS the VPS IP)
        try:
            with urllib.request.urlopen("https://api.ipify.org", timeout=10) as resp:
                public_ip = resp.read().decode().strip()
        except OSError as e:
            return f"⚠ Could not determine public IP: {e}"

        # Cache zone IDs so we don't re-fetch for subdomains of the same zone
        zone_cache: dict[str, str] = {}

        unchanged = 0
        updated: list[str] = []
        created: list[str] = []
        errors: list[str] = []

        for domain in domains:
            zone_id = self._cf_zone_id(token, domain, zone_cache)
            if not zone_id:
                errors.append(f"{domain}: zone not found")
                continue

            # Look up existing A record
            try:
                resp = self._cf_api(
                    token,
                    zone_id,
                    "GET",
                    f"dns_records?type=A&name={urllib.parse.quote(domain, safe='')}",
                )
            except OSError as e:
                errors.append(f"{domain}: {e}")
                continue

            if not resp.get("success"):
                errs = resp.get("errors", ["unknown"])
                errors.append(f"{domain}: {errs}")
                continue

            records = resp.get("result", [])
            if records:
                existing = records[0]
                if existing.get("content") == public_ip:
                    unchanged += 1
                    continue
                # Update
                body = {
                    "type": "A",
                    "name": domain,
                    "content": public_ip,
                    "ttl": 1,
                    "proxied": True,
                }
                try:
                    self._cf_api(
                        token, zone_id, "PUT", f"dns_records/{existing['id']}", body
                    )
                    updated.append(domain)
                except OSError as e:
                    errors.append(f"{domain}: update failed — {e}")
            else:
                # Create
                body = {
                    "type": "A",
                    "name": domain,
                    "content": public_ip,
                    "ttl": 1,
                    "proxied": True,
                }
                try:
                    self._cf_api(token, zone_id, "POST", "dns_records", body)
                    created.append(domain)
                except OSError as e:
                    errors.append(f"{domain}: create failed — {e}")

        parts: list[str] = []
        if updated:
            parts.append(f"{len(updated)} updated")
        if created:
            parts.append(f"{len(created)} created")
        if unchanged:
            parts.append(f"{unchanged} unchanged")
        summary = ", ".join(parts) if parts else "no records evaluated"

        lines = [f"{summary} ({public_ip})."]
        for err in errors:
            lines.append(f"  ⚠ {err}")

        return "\n".join(lines)

    def _docker_up(self) -> str | _Skipped | None:
        if self.skip_sudo:
            return SKIPPED
        if not (self._host_dir / ".env").exists():
            return SKIPPED
        subprocess.run(
            ["sudo", "docker", "compose", "up", "-d", "--remove-orphans"],
            cwd=self._host_dir,
            check=True,
        )
        return "Docker services started."

    def _ensure_cron(
        self, keyword: str, entry: str
    ) -> str | _Skipped | None:
        """Ensure *entry* is present in the user's crontab.

        Uses *keyword* to find an existing entry (matched by substring).
        Returns SKIPPED if the entry is already present, or a status string.
        """
        result = subprocess.run(
            ["crontab", "-l"], capture_output=True, text=True,
        )
        current = result.stdout if result.returncode == 0 else ""

        lines = [ln for ln in current.splitlines() if ln.strip()]

        for i, line in enumerate(lines):
            if keyword in line and not line.strip().startswith("#"):
                if line.strip() == entry:
                    return SKIPPED
                lines[i] = entry
                subprocess.run(
                    ["crontab", "-"], input="\n".join(lines) + "\n",
                    text=True, check=True,
                )
                return "updated"

        lines.append(entry)
        subprocess.run(
            ["crontab", "-"], input="\n".join(lines) + "\n",
            text=True, check=True,
        )
        return "added"

    def _setup_crons(self) -> str | _Skipped | None:
        """Ensure subconv.py and mirror.py cron entries exist, then show status."""
        subconv = (self._host_dir / "subconv" / "subconv.py")
        mirror = (self._host_dir / "mirror" / "mirror.py")

        jobs: list[tuple[str, str, Path]] = [
            ("subconv", "every 30 min", subconv),
            ("mirror",  "daily",          mirror),
        ]

        for name, schedule, script in jobs:
            entry = self._schedule_to_cron(schedule) + f" python3 {script.resolve()}"
            status = self._ensure_cron(name, entry)
            action = status  # "added", "updated", or SKIPPED
            logging.debug("cron %s: %s", name, "ok" if action == SKIPPED else action)

        lines = ["Cron jobs:"]
        for name, schedule, script in jobs:
            lines.append(f"  {name}: {schedule}  →  python3 {script.resolve()}")

        return "\n".join(lines)

    @staticmethod
    def _schedule_to_cron(schedule: str) -> str:
        """Convert a human schedule label to a cron expression."""
        return {
            "every 30 min": "*/30 * * * *",
            "daily": "0 3 * * *",
        }[schedule]

    def _tailscale_check(self) -> str | _Skipped | None:
        """If Tailscale is installed but not authenticated, print a hint."""
        if shutil.which("tailscale") is None:
            return "⚠ Tailscale not installed — run bootstrap script first."

        result = subprocess.run(
            ["tailscale", "status", "--json"], capture_output=True, text=True
        )
        if result.returncode != 0:
            return "⚠ tailscaled not running (check systemctl status tailscaled)."

        try:
            status = json.loads(result.stdout)
        except json.JSONDecodeError:
            return "⚠ Could not parse Tailscale status."

        backend = status.get("BackendState", "")
        if backend != "NeedsLogin":
            return SKIPPED

        return (
            "⚠ Tailscale not authenticated — run: sudo tailscale up"
        )



_ELEVATE_PS1 = """\
param(
    [switch]$Elevated,
    [string]$InstallPy,
    [string]$Python
)

$alreadyAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $alreadyAdmin) {
    $argList = @(
        "-ExecutionPolicy", "Bypass",
        "-File", $PSCommandPath,
        "-InstallPy", $InstallPy,
        "-Python", $Python,
        "-Elevated"
    )
    if ($args.Count -gt 0) {
        $argList += $args
    }
    $argString = ($argList | ForEach-Object {
        if ($_ -match '\\s') { '"{0}"' -f $_ } else { $_ }
    }) -join ' '

    $wt = Get-Command wt -ErrorAction SilentlyContinue
    if ($wt) {
        Start-Process wt -Verb runAs -ArgumentList (@("powershell") + $argList) -Wait
    } else {
        Start-Process powershell -Verb runAs -ArgumentList $argString -Wait
    }
    exit
}

Set-Location (Split-Path -Parent $InstallPy)
& $Python $InstallPy @args

if ($Elevated) {
    Write-Host ""
    Write-Host "Press Enter to exit."
    $null = Read-Host
}
"""


def _proxy_url(explicit: str | None = None) -> str | None:
    """Return a working proxy URL.

    Precedence: explicit argument > environment variables > probe 127.0.0.1:7897.
    """
    if explicit:
        return explicit
    for key in ("https_proxy", "HTTPS_PROXY", "http_proxy", "HTTP_PROXY"):
        url = os.environ.get(key)
        if url:
            return url
    try:
        with socket.create_connection(("127.0.0.1", 7897), timeout=1):
            return "http://127.0.0.1:7897"
    except OSError:
        return None


def _windows_symlink_capable() -> bool:
    """Return True if the current Windows session can create symlinks."""
    import ctypes

    if ctypes.windll.shell32.IsUserAnAdmin():
        return True
    try:
        import winreg

        with winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE,
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\AppModelUnlock",
        ) as key:
            value, _ = winreg.QueryValueEx(key, "AllowDevelopmentWithoutDevLicense")
            if value == 1:
                return True
    except FileNotFoundError:
        pass
    except OSError:
        pass
    return False


def _supports_ansi() -> bool:
    """Return True if stdout appears to support ANSI escape sequences."""
    if os.environ.get("NO_COLOR"):
        return False
    if not sys.stdout.isatty():
        return False
    if platform.system() != "Windows":
        return True
    return (
        "WT_SESSION" in os.environ
        or "ANSICON" in os.environ
        or "256color" in os.environ.get("TERM", "")
    )


def _environment() -> str:
    """Detect the environment based on username and OS."""
    user = getpass.getuser()
    system = platform.system()
    if user == "zyxir":
        return "personal"
    if user == "linuxuser" and system == "Linux":
        return "vps"
    if system == "Windows":
        return "corporate"
    return "personal"


if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Install Zyxir's dotfiles.")
    parser.add_argument("--debug", help="turn on debug mode", action="store_true")
    parser.add_argument(
        "--proxy", help="proxy URL for downloads (e.g. http://127.0.0.1:7897)"
    )
    parser.add_argument(
        "--skip-sudo",
        help="skip sudo operations (docker compose, etc.)",
        action="store_true",
    )
    args = parser.parse_args()
    debug: bool = args.debug

    # On Windows, hand off to the PowerShell wrapper if we cannot create symlinks
    if platform.system() == "Windows" and not _windows_symlink_capable():
        with tempfile.NamedTemporaryFile(mode="w", suffix=".ps1", delete=False) as f:
            f.write(_ELEVATE_PS1)
            ps1_path = f.name
        print("Elevating via PowerShell wrapper...")
        subprocess.run(
            [
                "powershell",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                ps1_path,
                "-InstallPy",
                str(Path(__file__).resolve()),
                "-Python",
                sys.executable,
            ]
            + sys.argv[1:]
        )
        try:
            os.unlink(ps1_path)
        except OSError:
            pass
        sys.exit(0)

    # Detect and configure proxy for downloads
    proxy_url = _proxy_url(args.proxy)
    proxy_status = ""
    if proxy_url:
        os.environ.setdefault("http_proxy", proxy_url)
        os.environ.setdefault("https_proxy", proxy_url)
        os.environ.setdefault("no_proxy", "localhost,127.0.0.1,::1")
        proxy_handler = urllib.request.ProxyHandler(
            {"http": proxy_url, "https": proxy_url}
        )
        urllib.request.install_opener(urllib.request.build_opener(proxy_handler))
        try:
            req = urllib.request.Request("https://github.com", method="HEAD")
            urllib.request.urlopen(req, timeout=5)
            proxy_status = " (reachable)"
        except Exception:
            proxy_status = " (unreachable)"

    # Setup logging
    tracker = setup_logging(debug=debug)

    # Detect ANSI support
    if _supports_ansi():
        C_SKIP = "\033[0;33m"
        C_DONE = "\033[1;32m"
        C_FAIL = "\033[1;31m"
        C_WARN = "\033[33m"
        C_INFO = "\033[1;36m"
        C_RESET = "\033[0m"
        C_CLEAR = "\033[1A\r"
    else:
        C_SKIP = C_DONE = C_FAIL = C_WARN = C_INFO = C_RESET = C_CLEAR = ""

    # Define platform-specific tasks
    env = _environment()
    proxy_display = (proxy_url or "none") + proxy_status
    print(
        f"{C_INFO}▶{C_RESET} Environment: {C_INFO}{env}{C_RESET}  |  Platform: {C_INFO}{platform.system()}{C_RESET}  |  Proxy: {C_INFO}{proxy_display}{C_RESET}"
    )
    print()

    tasks: list[Task] = []
    if platform.system() == "Darwin":
        tasks += [
            Git(),
            Ghostty(),
            Rime(),
            Vim(),
            Zsh(),
            Firefox(),
            VSCodium(),
            Fonts(),
        ]
    elif platform.system() == "Windows":
        tasks += [
            Git(),
            Rime(),
            PowerShell(),
            Vim(),
            VSCodium(),
            Firefox(),
            PowerToys(),
            Fonts(),
        ]
    elif platform.system() == "Linux":
        tasks += [
            Git(),
            Vim(),
            Zsh(),
            Rime(),
            VSCodium(),
            Fonts(),
        ]
        for host_dir in sorted(Path("./per_host").iterdir()):
            if host_dir.is_dir():
                tasks.append(VpsHost(host_dir.name, skip_sudo=args.skip_sudo))

    # Perform the tasks
    for task in tasks:
        if isinstance(task, AppTask) and env in task.skip_envs:
            continue
        if isinstance(task, HostTask) and not task.is_active:
            continue
        print_indented(f"{C_INFO}- {task.__doc__}...{C_RESET}", 0)
        try:
            for step in task.steps():
                indent += 2
                label = f"+ {step.description}..."
                print(f"{' ' * indent}{label}", flush=True)
                tracker.reset()
                result = step.run()
                if isinstance(result, _Skipped):
                    status = f"{C_SKIP}SKIP{C_RESET}"
                    hint = None
                else:
                    status = f"{C_DONE}DONE{C_RESET}"
                    hint = result
                if tracker.fired:
                    print_indented(status, 0)
                else:
                    print(f"{C_CLEAR}{' ' * indent}{label} {status}")
                if hint:
                    print_indented(hint, 2)
                indent -= 2
        except Exception as e:
            print_indented(f"{C_FAIL}FAILED{C_RESET} {C_WARN}{e}{C_RESET}", 2)
