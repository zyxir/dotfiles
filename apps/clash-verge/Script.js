// Clash Verge Rev Extension Script
// Edit below and refresh the profile in the app to apply.

function main(config, profileName) {

  if (!config) return config;

  overwriteDns(config);

  overwriteFakeIpFilter(config);

  overwriteTun(config);

  overwriteRules(config);

  return config;

}

// -- DNS constants -----------------------------------------------------------
//
// nameserver → domestic DoH (doh.pub) for direct traffic, DNS bootstrap.
// proxy-server-nameserver → foreign DoH through the proxy tunnel. Not all
//   may be reachable at any given time; Clash sends queries in parallel and
//   uses the fastest response.

const DIRECT_DOH = [
  "https://doh.pub/dns-query",               // DNSPod DoH, domestic
  "https://sm2.doh.pub/dns-query",           // DNSPod DoH (backup)
];

const PROXY_DOH = [
  "https://cloudflare-dns.com/dns-query",    // Cloudflare
  "https://dns.quad9.net/dns-query",         // Quad9
  "https://doh.mullvad.net/dns-query",       // Mullvad
  "https://dns.google/dns-query",            // Google
  "https://doh.opendns.com/dns-query",       // OpenDNS (Cisco)
  "https://dns.adguard-dns.com/dns-query",   // AdGuard
];

const BOOTSTRAP_RESOLVERS = [
  "9.9.9.9",                // Quad9 (privacy-focused, Swiss non-profit)
  "1.1.1.1",                // Cloudflare
  "8.8.8.8",                // Google
];

const NAMESERVER_POLICY = {
  "+.tail2b5f2.ts.net": ["100.100.100.100"],  // Tailscale MagicDNS

};

// -- DNS configuration -------------------------------------------------------

function overwriteDns(config) {

  // Bootstrap resolvers — plain UDP used only to resolve the DoH server
  // hostnames themselves. Actual DNS traffic goes through DoH afterward.
  config.dns = Object.assign({}, config.dns, {
    "default-nameserver": BOOTSTRAP_RESOLVERS,

    // Direct upstreams (non-proxied traffic)
    nameserver: DIRECT_DOH,

    // Upstreams for proxied traffic — routes through the proxy tunnel
    "proxy-server-nameserver": PROXY_DOH,

    // Fallback DNS — used when nameserver returns an IP outside fallback-filter
    fallback: DIRECT_DOH,

    // Per-domain nameserver overrides
    "nameserver-policy": NAMESERVER_POLICY,

    // Performance & privacy tweaks
    "prefer-h3": true,          // Use HTTP/3 for DoH when available (faster)
    "ipv6": false,              // Disable AAAA lookups
    "use-hosts": false,         // Don't leak /etc/hosts to the proxy
    "use-system-hosts": false,
  });

}

// -- Fake-IP filter constants -------------------------------------------------
//
// Domains that must resolve to real IPs — they are excluded from the fake-ip
// range. Without these, local services (mDNS, Tailscale, STUN, game consoles,
// captive portals) would receive synthetic addresses and break.

const FAKE_IP_FILTER = [
  // Local / mDNS / IoT
  "+.local",
  "+.lan",
  "+.internal",
  "+.localdomain",
  "home.arpa",
  "+.bogon",
  "+.m2m",

  // Tailscale MagicDNS
  "+.tail2b5f2.ts.net",

  // AdGuard local filtering
  "injections.adguard.org",
  "local.adguard.org",

  // STUN / TURN (WebRTC — requires real IPs for peer connection)
  "stun.*",
  "*.stun.*",
  "*.turn.*",

  // Game consoles
  "*.srv.nintendo.net",
  "*.stun.playstation.net",
  "xbox.*.microsoft.com",
  "*.xboxlive.com",

  // Steam LAN cache
  "lancache.steamcontent.com",

  // Microsoft network connectivity check (NCSI)
  "dns.msftncsi.com",

  // Apple push notifications
  "+.push.apple.com",
];

// -- Fake-IP filter configuration -------------------------------------------

function overwriteFakeIpFilter(config) {

  config.dns["fake-ip-filter"] = FAKE_IP_FILTER;

}

// -- TUN constants ------------------------------------------------------------

const TUN_OPTIONS = {
  // TUN mode itself is activated in the app GUI (requires privileged service).
  // The settings below take effect once the user enables it.
  stack: "system",
  device: "tun0",
  "dns-hijack": ["any:53", "tcp://any:53"],
  "auto-route": true,
  "auto-detect-interface": true,
  "strict-route": true,
  // Exclude private / VPN / Docker subnets from the tunnel as needed.
  // Example: ["10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16"]
  "route-exclude-address": [],
};

// -- TUN configuration -------------------------------------------------------

function overwriteTun(config) {

  config.tun = Object.assign({}, config.tun, TUN_OPTIONS);

}

// -- Custom rules ------------------------------------------------------------

function overwriteRules(config) {

  // Prepend rules here. Example:
  //
  //   config.rules = [
  //     "DOMAIN-SUFFIX,example.com,Proxy",
  //     ...config.rules,
  //   ];

}
