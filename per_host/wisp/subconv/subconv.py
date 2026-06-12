#!/usr/bin/env python3
"""Fetch Clash subscription, transform via Script.js, write static YAML.

This script is the VPS-side counterpart to per_app/clash-verge/Script.js.
It runs the *same* Script.js logic through Node.js so both workflows stay
in sync — edit Script.js once, both per-device and centralized methods
pick up the change.

Requires: python3-yaml, nodejs   (installed by bootstrap/vps/vps_bootstrap.sh)
Output:  ./srv/<secret>/ZyProxy (served by Caddy from subconv/ root)

The installer creates a cron job that runs this script every 30 min.
"""

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

# Third-party — apt install python3-yaml
import yaml

# --- Configuration ----------------------------------------------------

HERE = Path(__file__).resolve().parent
SCRIPT_JS = HERE / "Script.js"
OUTPUT_DIR = HERE   # set to HERE/SECRET below

# Read domain from parent .env for printing access URLs
DOTENV = HERE.parent / ".env"
DOMAIN = None
if DOTENV.is_file():
    for line in DOTENV.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line.startswith("DOMAIN="):
            DOMAIN = line.split("=", 1)[1].strip().strip('"').strip("'")

# Read configuration from subconv.env (separate file — changes more often
# than .env passwords)
SUB_ENV = HERE / "subconv.env"

# Parse all env vars into a dict
_env_vars = {}
if SUB_ENV.is_file():
    for _line in SUB_ENV.read_text(encoding="utf-8").splitlines():
        _line = _line.strip()
        if "=" in _line and not _line.startswith("#"):
            _key, _, _val = _line.partition("=")
            _env_vars[_key.strip()] = _val.strip().strip('"').strip("'")

SECRET = _env_vars.get("SECRET")

SUBSCRIPTION_URLS = []
i = 1
while f"SUBSCRIPTION_URL_{i}" in _env_vars:
    url = _env_vars[f"SUBSCRIPTION_URL_{i}"]
    if url:
        SUBSCRIPTION_URLS.append(url)
    i += 1

if not SUBSCRIPTION_URLS:
    print(f"Error: No SUBSCRIPTION_URL_1 (etc.) found in {SUB_ENV}", file=sys.stderr)
    sys.exit(1)
if not SECRET:
    print(f"Error: SECRET not found in {SUB_ENV}", file=sys.stderr)
    sys.exit(1)

OUTPUT_DIR = HERE / "srv" / SECRET
OUTPUT_FILE = OUTPUT_DIR / "ZyProxy"

# --- Fetch & merge all subscriptions ----------------------------------

UPSTREAM_STRIP = (
    "external-controller", "secret", "allow-lan", "redir-port",
    "interval", "port", "socks-port", "mode", "log-level", "ipv6",
)

all_proxies = []          # merged proxy list
seen_names = set()        # for dedup-rename
base_config = None        # first successful config (minus proxies)

for idx, url in enumerate(SUBSCRIPTION_URLS, start=1):
    label = f"[{idx}/{len(SUBSCRIPTION_URLS)}]"

    # --- Fetch ---
    print(f"{label} Fetching: {url}")
    req = Request(url, headers={"User-Agent": "ClashVerge/2.0"})
    try:
        with urlopen(req, timeout=15) as resp:
            raw_yaml = resp.read().decode("utf-8")
    except HTTPError as e:
        print(f"{label}  WARNING: upstream returned {e.code}, skipping", file=sys.stderr)
        continue
    except (URLError, OSError) as e:
        print(f"{label}  WARNING: cannot reach upstream: {e}, skipping", file=sys.stderr)
        continue

    # --- Parse ---
    try:
        config = yaml.safe_load(raw_yaml)
    except yaml.YAMLError as e:
        print(f"{label}  WARNING: invalid YAML: {e}, skipping", file=sys.stderr)
        continue

    if not isinstance(config, dict) or "proxies" not in config:
        print(f"{label}  WARNING: missing 'proxies', skipping", file=sys.stderr)
        continue

    upstream_proxies = config.get("proxies", [])
    if not upstream_proxies:
        print(f"{label}  WARNING: 0 proxies in this subscription, skipping", file=sys.stderr)
        continue

    # --- Merge proxies with rename-on-collision ---
    added = 0
    renamed = 0
    for proxy in upstream_proxies:
        name = proxy.get("name", "")
        if not name:
            continue
        if name in seen_names:
            proxy = dict(proxy)                           # shallow copy
            proxy["name"] = f"{name} (sub{idx})"
            renamed += 1
        seen_names.add(proxy["name"])
        all_proxies.append(proxy)
        added += 1

    suffix = f" ({added} proxies, {renamed} renamed)" if renamed else f" ({added} proxies)"
    print(f"{label}  OK{suffix}")

    # Use first successful config as the base (Script.js only reads proxies;
    # other upstream fields are stripped or overwritten anyway)
    if base_config is None:
        for key in UPSTREAM_STRIP:
            config.pop(key, None)
        base_config = config

# --- Check we have something to work with ---

if not all_proxies:
    print("Error: 0 proxies after merging all subscriptions", file=sys.stderr)
    sys.exit(1)

if base_config is None:
    print("Error: no subscription could be fetched", file=sys.stderr)
    sys.exit(1)

base_config["proxies"] = all_proxies
print(f"Total: {len(all_proxies)} proxies from {len(SUBSCRIPTION_URLS)} subscription(s)")

config_json = json.dumps(base_config, ensure_ascii=False)

# --- Load Script.js (the canonical transform logic) -------------------

if not SCRIPT_JS.is_file():
    print(f"Error: Script.js not found at {SCRIPT_JS}", file=sys.stderr)
    sys.exit(1)

script_js = SCRIPT_JS.read_text(encoding="utf-8")

# --- Build + run Node.js transform ------------------------------------

# Append a tiny CLI wrapper that reads config from stdin and writes
# the result to stdout.  No npm dependencies — Script.js is pure JS.
wrapper = """
const fs = require('fs');
const config = JSON.parse(fs.readFileSync(0, 'utf-8'));
main(config, 'default');
process.stdout.write(JSON.stringify(config));
"""

try:
    with tempfile.NamedTemporaryFile(mode="w", suffix=".js", delete=False) as f:
        f.write(script_js)
        f.write(wrapper)
        node_script = f.name

    result = subprocess.run(
        ["node", node_script],
        input=config_json,
        capture_output=True,
        text=True,
        timeout=30,
    )
finally:
    os.unlink(node_script)

if result.returncode != 0:
    print(f"Error: Node.js transform failed:\n{result.stderr}", file=sys.stderr)
    sys.exit(1)

# --- Parse transformed JSON → YAML, write output ----------------------

try:
    transformed = json.loads(result.stdout)
except json.JSONDecodeError as e:
    print(f"Error: invalid JSON from transform: {e}", file=sys.stderr)
    sys.exit(1)

try:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
except PermissionError:
    print(f"Error: Cannot write to {OUTPUT_DIR.parent} — "
          f"it may be owned by root (Docker creates it on first run).\n"
          f"Fix: sudo chown -R $(whoami) {OUTPUT_DIR.parent}",
          file=sys.stderr)
    sys.exit(1)

output_yaml = yaml.dump(transformed, allow_unicode=True, sort_keys=False)

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    f.write(output_yaml)

print(f"Written {len(output_yaml)} bytes to {OUTPUT_FILE}")
if DOMAIN:
    print(f"  https://subconv.{DOMAIN}/{SECRET}/ZyProxy")
