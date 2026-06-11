#!/usr/bin/python3
"""Benchmark DoH servers for Clash nameserver selection.

Tests every DoH provider in both DIRECT and PROXY modes using RFC 8484
wire format (application/dns-message) via HTTP/2 as the RFC requires.

All servers and queries run concurrently — results print as each server
completes, and the full benchmark finishes in ~3 seconds regardless of
how many servers are tested.
"""

import base64
import os
import socket
import subprocess
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

SERVERS = [
    # Domestic
    ("DNSPod",          "https://doh.pub/dns-query"),
    ("AliDNS",          "https://dns.alidns.com/dns-query"),
    ("360",             "https://doh.360.cn/dns-query"),
    # Foreign
    ("Quad9",           "https://dns.quad9.net/dns-query"),
    ("Cloudflare",      "https://cloudflare-dns.com/dns-query"),
    ("Google",          "https://dns.google/dns-query"),
    ("NextDNS",         "https://dns.nextdns.io"),
    ("Mullvad",         "https://doh.mullvad.net/dns-query"),
    ("DNS.SB",          "https://doh.dns.sb/dns-query"),
    ("AdGuard",         "https://dns.adguard-dns.com/dns-query"),
]

DOMAINS = [
    "baidu.com",
    "google.com",
]

TIMEOUT = 3
PROXY = "http://127.0.0.1:7897"

GREEN  = "\033[32m"
YELLOW = "\033[33m"
RED    = "\033[31m"
RESET  = "\033[0m"


def build_dns_query(domain: str) -> bytes:
    """Build a DNS wire-format query for an A record, with EDNS(0)."""
    header = b"\x00\x00\x01\x00\x00\x01\x00\x00\x00\x00\x00\x01"
    qname = b"".join(
        bytes([len(part)]) + part.encode("ascii")
        for part in domain.rstrip(".").split(".")
    ) + b"\x00"
    question = qname + b"\x00\x01\x00\x01"
    edns = b"\x00\x00\x29\x02\x00\x00\x00\x00\x00\x00\x00"
    return header + question + edns


def parse_dns_response(data: bytes) -> list[str]:
    """Extract A record IPs from a DNS wire-format response. Best-effort."""
    ips = []
    try:
        pos = 12
        while pos < len(data) and data[pos] != 0:
            pos += data[pos] + 1
        pos += 5
        ancount = (data[6] << 8) | data[7]
        for _ in range(ancount):
            if pos + 10 > len(data):
                break
            if data[pos] & 0xc0 == 0xc0:
                pos += 2
            else:
                while pos < len(data) and data[pos] != 0:
                    pos += data[pos] + 1
                pos += 1
            if pos + 10 > len(data):
                break
            rtype = (data[pos] << 8) | data[pos + 1]
            rdlength = (data[pos + 8] << 8) | data[pos + 9]
            pos += 10
            if pos + rdlength > len(data):
                break
            if rtype == 1 and rdlength == 4:
                ips.append(".".join(str(b) for b in data[pos : pos + 4]))
            pos += rdlength
    except (IndexError, ValueError):
        pass
    return ips


def proxy_available() -> bool:
    host, port = PROXY.replace("http://", "").split(":")
    try:
        with socket.create_connection((host, int(port)), timeout=1):
            return True
    except OSError:
        return False


def test_one(url: str, domain: str, use_proxy: bool) -> tuple[str, str]:
    """Run a single DoH query. Returns (result_string, color_code)."""
    query = build_dns_query(domain)
    encoded = base64.urlsafe_b64encode(query).rstrip(b"=").decode()
    doh_url = f"{url}?dns={encoded}"

    cmd = [
        "curl", "-sS", "--max-time", str(TIMEOUT),
        "--http2",
        "-H", "Accept: application/dns-message",
        "-H", "User-Agent:",
        "-w", "%{http_code}",
    ]
    if not use_proxy:
        cmd += ["--noproxy", "*"]

    with tempfile.NamedTemporaryFile(delete=False) as f:
        body_path = f.name

    cmd += ["-o", body_path, doh_url]

    env = os.environ.copy()
    if use_proxy:
        env["http_proxy"] = PROXY
        env["https_proxy"] = PROXY
    else:
        env.pop("http_proxy", None)
        env.pop("https_proxy", None)

    start = time.monotonic()
    result = subprocess.run(cmd, capture_output=True, text=True, env=env,
                            timeout=TIMEOUT + 3)
    latency = (time.monotonic() - start) * 1000

    http_code = result.stdout.strip()

    try:
        with open(body_path, "rb") as f:
            body = f.read()
    finally:
        try:
            os.unlink(body_path)
        except OSError:
            pass

    if http_code == "200":
        ips = parse_dns_response(body)
        if ips:
            return f"{latency:.0f}ms ✓", GREEN
        else:
            return f"{latency:.0f}ms NODATA", YELLOW
    elif http_code == "000":
        if result.returncode == 28:
            return "timeout", RED
        if result.returncode == 35:
            return "reset", RED
        if result.returncode == 7:
            return "refused", RED
        return "unreach", RED
    elif http_code in ("400", "403", "404", "500", "502", "503"):
        body_text = body[:100].decode("utf-8", errors="replace")
        if "HTTP/2" in body_text:
            return "H2 only", RED
        if "<html" in body_text.lower():
            return "blocked", RED
        return f"HTTP {http_code}", RED
    elif http_code == "505":
        return "H2 only", RED
    else:
        return f"HTTP {http_code}", RED


def test_server(
    label: str, url: str, domains: list[str], have_proxy: bool,
) -> tuple[str, list[tuple[str, str]]]:
    """Test all domains × modes for one server concurrently. Returns (label, cells)."""
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures: list[tuple[int, object]] = []  # (column_index, future)
        col = 0

        for domain in domains:
            futures.append((col, executor.submit(test_one, url, domain, False)))
            col += 1
        if have_proxy:
            for domain in domains:
                futures.append((col, executor.submit(test_one, url, domain, True)))
                col += 1

        # Sort by column index to preserve domain/mode order
        futures.sort(key=lambda x: x[0])
        cells = [f.result() for _, f in futures]

    return label, cells


def main() -> None:
    print("DoH Benchmark (RFC 8484 wire format, HTTP/2)")
    print(f"  {GREEN}✓{RESET} resolved  {YELLOW}NODATA{RESET} no A record  {RED}error{RESET} unreachable")

    have_proxy = proxy_available()

    cols = [(d, "DIRECT") for d in DOMAINS]
    if have_proxy:
        cols += [(d, "PROXY") for d in DOMAINS]

    name_w = max(len(s[0]) for s in SERVERS)
    col_w = max(len(d) + 8 for d in DOMAINS)

    header_labels = [f"{d} ({m})" for d, m in cols]
    header = f"  {'':<{name_w}}  " + "  ".join(f"{label:>{col_w}}" for label in header_labels)
    print(header)
    print("  " + "─" * (name_w + 2 + len(cols) * (col_w + 2)))

    # Run all servers concurrently; print rows as they complete
    with ThreadPoolExecutor(max_workers=len(SERVERS)) as executor:
        future_to_label = {
            executor.submit(test_server, label, url, DOMAINS, have_proxy): label
            for label, url in SERVERS
        }
        for future in as_completed(future_to_label):
            label, cells = future.result()
            row = f"  {label:<{name_w}}  "
            row += "  ".join(f"{color}{text:>{col_w}}{RESET}" for text, color in cells)
            print(row, flush=True)


if __name__ == "__main__":
    main()
