#!/usr/bin/env python3
"""Fetch Clash subscription, transform via Script.js, write static YAML.

This script is the VPS-side counterpart to per_app/clash-verge/Script.js.
It runs the *same* Script.js logic through Node.js so both workflows stay
in sync — edit Script.js once, both per-device and centralized methods
pick up the change.

Requires: python3-yaml, nodejs   (installed by bootstrap/vps/vps_bootstrap.sh)
Output:  ./secret/<secret>/ZyProxy (served by Caddy from subconv/ root)

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

# Read configuration from subconv.env (separate file — changes more often
# than .env passwords)
SUB_ENV = HERE / "subconv.env"
SUBSCRIPTION_URL = None
SECRET = None
if SUB_ENV.is_file():
    for line in SUB_ENV.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line.startswith("SUBSCRIPTION_URL="):
            SUBSCRIPTION_URL = line.split("=", 1)[1].strip().strip('"').strip("'")
        elif line.startswith("SECRET="):
            SECRET = line.split("=", 1)[1].strip().strip('"').strip("'")

if not SUBSCRIPTION_URL:
    print(f"Error: SUBSCRIPTION_URL not found in {SUB_ENV}", file=sys.stderr)
    sys.exit(1)
if not SECRET:
    print(f"Error: SECRET not found in {SUB_ENV}", file=sys.stderr)
    sys.exit(1)

OUTPUT_DIR = HERE / "secret" / SECRET
OUTPUT_FILE = OUTPUT_DIR / "ZyProxy"

# --- Fetch upstream subscription --------------------------------------

print(f"Fetching subscription...")
req = Request(SUBSCRIPTION_URL, headers={"User-Agent": "ClashVerge/2.0"})
try:
    with urlopen(req, timeout=15) as resp:
        raw_yaml = resp.read().decode("utf-8")
except HTTPError as e:
    print(f"Error: upstream returned {e.code}", file=sys.stderr)
    sys.exit(1)
except (URLError, OSError) as e:
    print(f"Error: cannot reach upstream: {e}", file=sys.stderr)
    sys.exit(1)

# --- Parse upstream YAML → JSON (for Node interop) --------------------

try:
    config = yaml.safe_load(raw_yaml)
except yaml.YAMLError as e:
    print(f"Error: invalid YAML from upstream: {e}", file=sys.stderr)
    sys.exit(1)

if not isinstance(config, dict) or "proxies" not in config:
    print("Error: upstream config missing 'proxies'", file=sys.stderr)
    sys.exit(1)

print(f"Loaded {len(config['proxies'])} proxies")

# Strip upstream fields that would leak into client configs as defaults
for key in ("external-controller", "secret", "allow-lan", "redir-port",
            "interval", "port", "socks-port", "mode", "log-level", "ipv6"):
    config.pop(key, None)

config_json = json.dumps(config, ensure_ascii=False)

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
