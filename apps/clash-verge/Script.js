// Global Extension Script for Clash Verge Rev
// Edit below and refresh the profile in the app to apply.

function main(config, profileName) {

  // -- Hardened DNS over HTTPS -----------------------------------------------
  //
  // Direct connections use domestic DoH (foreign servers blocked from CN).
  // Proxy-tunneled connections use foreign DoH (privacy, no logging).

  var dohDirect = [
    "https://doh.360.cn/dns-query",            // fast, domestic
    "https://doh.apad.pro/dns-query",          // domestic, slower fallback
  ];

  var dohProxy = [
    "https://dns.quad9.net/dns-query",         // Quad9 (security)
    "https://doh.mullvad.net/dns-query",       // Mullvad (privacy)
  ];

  config.dns = Object.assign({}, config.dns, {
    // Bootstrap resolvers — plain UDP used only to resolve the DoH server
    // hostnames themselves. Actual DNS traffic goes through DoH afterward.
    "default-nameserver": [
      "9.9.9.9",                // Quad9 (privacy-focused, Swiss non-profit)
      "1.1.1.1",                // Cloudflare
      "8.8.8.8",                // Google
    ],

    // Direct upstreams (non-proxied traffic)
    nameserver: dohDirect,

    // Upstreams for proxied traffic — routes through the proxy tunnel
    "proxy-server-nameserver": dohProxy,

    // Fallback DNS — used when nameserver returns an IP outside fallback-filter
    fallback: dohDirect,

    // Tailscale hostnames → Tailscale MagicDNS
    "nameserver-policy": {
      "+.tail2b5f2.ts.net": ["100.100.100.100"],
    },

    // Performance & privacy tweaks
    "prefer-h3": true,          // Use HTTP/3 for DoH when available (faster)
    "ipv6": false,              // Disable AAAA lookups unless you need IPv6
    "use-hosts": false,         // Don't leak /etc/hosts to the proxy
    "use-system-hosts": false,
  });

  // -- Custom rules -----------------------------------------------------------
  // Prepend rules here. Example:
  //
  //   config.rules = [
  //     "DOMAIN-SUFFIX,example.com,Proxy",
  //     ...config.rules,
  //   ];

  return config;
}
