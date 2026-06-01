#!/usr/bin/python3
"""Benchmark DoH servers for Clash nameserver selection.

Tests domestic DoH servers directly and foreign DoH servers through the proxy
(127.0.0.1:7897). Foreign servers are skipped if the proxy is unavailable.
"""

import json
import socket
import time
import urllib.error
import urllib.request

# Servers reachable directly from CN
DIRECT_SERVERS = [
    ("DNSPod",          "https://doh.pub/dns-query",          "name"),
    ("DNSPod backup",   "https://sm2.doh.pub/dns-query",      "name"),
    ("360",             "https://doh.360.cn/dns-query",       "name"),
    ("AliDNS",          "https://dns.alidns.com/dns-query",   "name"),
]

# Servers that need a proxy from CN
PROXY_SERVERS = [
    ("Quad9",           "https://dns.quad9.net/dns-query",    "name"),
    ("Mullvad",         "https://doh.mullvad.net/dns-query",  "name"),
    ("Cloudflare",      "https://cloudflare-dns.com/dns-query", "name"),
    ("Google",          "https://dns.google/dns-query",       "name"),
]

DOMAINS = [
    ("baidu.com",       "domestic"),
    ("google.com",      "foreign"),
    ("cloudflare.com",  "foreign-cdn"),
]

TIMEOUT = 5
PROXY_HOST = "127.0.0.1"
PROXY_PORT = 7897


def proxy_available() -> bool:
    """Check if the proxy port is listening."""
    try:
        with socket.create_connection((PROXY_HOST, PROXY_PORT), timeout=1):
            return True
    except OSError:
        return False


def build_opener(use_proxy: bool) -> urllib.request.OpenerDirector:
    """Build a URL opener, optionally routing through the proxy."""
    if use_proxy:
        proxy_url = f"http://{PROXY_HOST}:{PROXY_PORT}"
        handler = urllib.request.ProxyHandler({"http": proxy_url, "https": proxy_url})
        return urllib.request.build_opener(handler)
    return urllib.request.build_opener()


def test_doh(url: str, param: str, domain: str, opener: urllib.request.OpenerDirector) -> tuple:
    """Query a DoH server for an A record.

    Returns (latency_ms | None, ips: list[str], error: str | None).
    """
    query = f"{url}?{param}={domain}&type=A"
    req = urllib.request.Request(query)
    req.add_header("Accept", "application/dns-json")

    start = time.monotonic()
    try:
        with opener.open(req, timeout=TIMEOUT) as resp:
            raw = resp.read()
            latency = (time.monotonic() - start) * 1000
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                return None, [], "invalid JSON (not DoH?)"
            if "Answer" in data:
                ips = [a["data"] for a in data["Answer"] if a["type"] == 1]
                return latency, ips, None
            else:
                return latency, [], f"no answer (status={data.get('Status', '?')})"

    except urllib.error.HTTPError as e:
        body = e.read(500).decode("utf-8", errors="replace")
        if "<html" in body.lower() or "<!doctype" in body.lower():
            return None, [], "blocked (HTML response)"
        return None, [], f"HTTP {e.code}"

    except urllib.error.URLError as e:
        reason = str(e.reason)
        if "timed out" in reason.lower():
            return None, [], "timeout"
        return None, [], f"unreachable ({reason})"

    except Exception as e:
        return None, [], str(e)


def run_tests(servers: list, opener: urllib.request.OpenerDirector, label: str) -> None:
    """Run benchmarks for a group of servers."""
    print(f"\n{label}")
    print("=" * 72)

    for domain, category in DOMAINS:
        print(f"\n  {category}: {domain}\n")
        header = f"  {'Server':<18} {'Latency':>9}  {'IPs':<18} Status"
        print(header)
        print("  " + "-" * 68)

        for label_, url, param in servers:
            latency, ips, err = test_doh(url, param, domain, opener)

            if err:
                print(f"  {label_:<18} {'—':>9}  {'—':<18} {err}")
            elif not ips:
                print(f"  {label_:<18} {latency:>8.0f}ms  {'—':<18} NODATA")
            else:
                print(f"  {label_:<18} {latency:>8.0f}ms  {ips[0]:<18} {len(ips)} IP(s)")


def main() -> None:
    print("DoH Server Benchmark")
    print("=" * 72)

    # Direct tests
    run_tests(DIRECT_SERVERS, build_opener(use_proxy=False), "DIRECT (no proxy)")

    # Proxy tests
    if proxy_available():
        run_tests(PROXY_SERVERS, build_opener(use_proxy=True), f"PROXIED (http://{PROXY_HOST}:{PROXY_PORT})")
    else:
        print(f"\nPROXY SKIPPED — {PROXY_HOST}:{PROXY_PORT} not reachable.")

    print("\nDone.")
    print("DIRECT_DOH:  pick fast, reachable servers from the DIRECT group.")
    print("PROXY_DOH:   pick servers from the PROXIED group that resolve google.com correctly.")


if __name__ == "__main__":
    main()
