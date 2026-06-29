#!/usr/bin/env python3
"""Refresh only the hosts: section of the ZyProxy Clash config.

Runs `tailscale status --json`, builds a hosts mapping from peer DNS
names to their first Tailscale IP, and updates the existing ZyProxy
YAML in-place.  No external network requests — safe to run every 2 min.

Requires: python3-yaml   (installed by bootstrap/vps/vps_bootstrap.sh)
"""

import json
import subprocess
import sys
from pathlib import Path

# Third-party — apt install python3-yaml
import yaml

HERE = Path(__file__).resolve().parent

# --- Read SECRET from subconv.env ---------------------------------------

_env_vars = {}
_sub_env = HERE / "subconv.env"
if _sub_env.is_file():
    for _line in _sub_env.read_text(encoding="utf-8").splitlines():
        _line = _line.strip()
        if "=" in _line and not _line.startswith("#"):
            _key, _, _val = _line.partition("=")
            _env_vars[_key.strip()] = _val.strip().strip('"').strip("'")

SECRET = _env_vars.get("SECRET")
if not SECRET:
    print("Error: SECRET not found in subconv.env", file=sys.stderr)
    sys.exit(1)

OUTPUT_FILE = HERE / "srv" / SECRET / "ZyProxy"
if not OUTPUT_FILE.is_file():
    # subconv.py hasn't generated a config yet — nothing to refresh
    sys.exit(0)

# --- Query Tailscale -----------------------------------------------------

try:
    result = subprocess.run(
        ["tailscale", "status", "--json"],
        capture_output=True, text=True, timeout=5,
    )
except (FileNotFoundError, subprocess.TimeoutExpired):
    sys.exit(0)  # tailscale not available — don't touch existing hosts

if result.returncode != 0:
    sys.exit(0)

try:
    status = json.loads(result.stdout)
except json.JSONDecodeError:
    sys.exit(0)

self_dns = status.get("Self", {}).get("DNSName", "")
if not self_dns or "." not in self_dns:
    sys.exit(0)

suffix = self_dns.split(".", 1)[1].rstrip(".")
if not suffix:
    sys.exit(0)

hosts = {}

# Self (the VPS)
self_host = status.get("Self", {})
_self_dns = self_host.get("DNSName", "").rstrip(".")
_self_ips = self_host.get("TailscaleIPs", [])
if _self_dns and _self_ips:
    # Prefer IPv4 — services often bind only on IPv4.
    _v4 = [ip for ip in _self_ips if ":" not in ip]
    hosts[_self_dns] = _v4[0] if _v4 else _self_ips[0]

# Peers
for peer in status.get("Peer", {}).values():
    dns_name = peer.get("DNSName", "").rstrip(".")
    ips = peer.get("TailscaleIPs", [])
    if dns_name and ips:
        _v4 = [ip for ip in ips if ":" not in ip]
        hosts[dns_name] = _v4[0] if _v4 else ips[0]

# --- Update the YAML -----------------------------------------------------

try:
    config = yaml.safe_load(OUTPUT_FILE.read_text(encoding="utf-8"))
except (yaml.YAMLError, OSError):
    sys.exit(0)

if not isinstance(config, dict):
    sys.exit(0)

# Only write if something changed
old = config.get("hosts", {})
if old == hosts:
    sys.exit(0)

config["hosts"] = hosts

try:
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    output_yaml = yaml.dump(config, allow_unicode=True, sort_keys=False)
    OUTPUT_FILE.write_text(output_yaml, encoding="utf-8")
except OSError:
    sys.exit(0)

print(f"Refresh hosts: {len(hosts)} device(s) (suffix={suffix})")
