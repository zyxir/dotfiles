#!/usr/bin/python3
"""Benchmark DoH servers for Clash nameserver selection.

Tests domestic DoH servers directly and foreign DoH servers through the proxy
(127.0.0.1:7897). Foreign servers are skipped if the proxy is unavailable.
"""

import json
import re
import socket
import time
import urllib.error
import urllib.request

DIRECT_SERVERS = [
    ("DNSPod",          "https://doh.pub/dns-query",          "name"),
    ("DNSPod backup",   "https://sm2.doh.pub/dns-query",      "name"),
    ("360",             "https://doh.360.cn/dns-query",       "name"),
    ("AliDNS",          "https://dns.alidns.com/dns-query",   "name"),
]

PROXY_SERVERS = [
    ("Cloudflare",      "https://cloudflare-dns.com/dns-query", "name"),
    ("Quad9",           "https://dns.quad9.net/dns-query",    "name"),
    ("Mullvad",         "https://doh.mullvad.net/dns-query",  "name"),
    ("Google",          "https://dns.google/dns-query",       "name"),
    ("OpenDNS",         "https://doh.opendns.com/dns-query",  "name"),
    ("AdGuard",         "https://dns.adguard-dns.com/dns-query", "name"),
]

DOMAINS = [
    ("baidu.com",       "baidu"),
    ("google.com",      "google"),
    ("cloudflare.com",  "cf"),
]

TIMEOUT = 5
PROXY_HOST = "127.0.0.1"
PROXY_PORT = 7897

GREEN  = "\033[32m"
YELLOW = "\033[33m"
RED    = "\033[31m"
RESET  = "\033[0m"


def proxy_available() -> bool:
    try:
        with socket.create_connection((PROXY_HOST, PROXY_PORT), timeout=1):
            return True
    except OSError:
        return False


def build_opener(use_proxy: bool) -> urllib.request.OpenerDirector:
    if use_proxy:
        proxy_url = f"http://{PROXY_HOST}:{PROXY_PORT}"
        return urllib.request.build_opener(
            urllib.request.ProxyHandler({"http": proxy_url, "https": proxy_url})
        )
    return urllib.request.build_opener()


def visible_len(s: str) -> int:
    return len(re.sub(r"\033\[[0-9;]*m", "", s))


def test_doh(url: str, param: str, domain: str, opener: urllib.request.OpenerDirector) -> tuple:
    """Returns (plain_string, color_code)."""
    query = f"{url}?{param}={domain}&type=A"
    req = urllib.request.Request(query)
    req.add_header("Accept", "application/dns-json")

    start = time.monotonic()
    try:
        with opener.open(req, timeout=TIMEOUT) as resp:
            raw = resp.read()
            latency = (time.monotonic() - start) * 1000
            data = json.loads(raw)
            answers = data.get("Answer", [])
            ips = [a["data"] for a in answers if a["type"] == 1]
            if ips:
                return f"{latency:.0f}ms ✓", GREEN
            else:
                return f"{latency:.0f}ms NODATA", YELLOW
    except urllib.error.HTTPError as e:
        body = e.read(500).decode("utf-8", errors="replace")
        msg = "blocked" if "<html" in body.lower() else f"HTTP{e.code}"
        return msg, RED
    except urllib.error.URLError as e:
        msg = "timeout" if "timed out" in str(e.reason).lower() else "unreach"
        return msg, RED
    except json.JSONDecodeError:
        return "bad JSON", RED
    except Exception as e:
        return str(e)[:12], RED


def run_tests(servers: list, opener: urllib.request.OpenerDirector, label: str) -> None:
    name_w = max(len(s[0]) for s in servers)
    col_w = max(len(d[0]) + 4 for d in DOMAINS)  # domain text + " Xms ✓"
    col_w = max(col_w, 10)

    print(f"\n{label}")
    header = f"  {'':<{name_w}}  " + "  ".join(f"{d[1]:>{col_w}}" for d in DOMAINS)
    print(header)
    print("  " + "─" * (name_w + 2 + len(DOMAINS) * (col_w + 2)))

    for label_, url, param in servers:
        cells = []
        for domain, _ in DOMAINS:
            text, color = test_doh(url, param, domain, opener)
            cells.append((text, color))

        row = f"  {label_:<{name_w}}  "
        row += "  ".join(f"{color}{text:>{col_w}}{RESET}" for text, color in cells)
        print(row)


def main() -> None:
    print("DoH Benchmark")
    print(f"  {GREEN}✓{RESET} resolved  {YELLOW}NODATA{RESET} no A record  {RED}error{RESET} unreachable")

    run_tests(DIRECT_SERVERS, build_opener(use_proxy=False), "DIRECT")

    if proxy_available():
        run_tests(PROXY_SERVERS, build_opener(use_proxy=True), "PROXY")
    else:
        print(f"\nPROXY {YELLOW}skipped{RESET} — {PROXY_HOST}:{PROXY_PORT} not reachable")


if __name__ == "__main__":
    main()
