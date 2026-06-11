// Clash Verge Rev Extension Script
// Edit below and refresh the profile in the app to apply.

function main(config, profileName) {

  if (!config) return config;

  overwriteDns(config);

  overwriteTun(config);

  overwriteProxyGroups(config);

  overwriteRules(config);

  return config;

}

// ===========================================================================
// DNS
// ===========================================================================

const DIRECT_DOH = [
  "https://dns.alidns.com/dns-query",         // AliDNS, domestic
  "https://doh.pub/dns-query",               // DNSPod DoH, domestic
  "https://doh.360.cn/dns-query",            // 360 DoH, domestic
];

const PROXY_DOH = [
  "https://dns.nextdns.io",                  // NextDNS
  "https://cloudflare-dns.com/dns-query",    // Cloudflare
  "https://dns.quad9.net/dns-query",         // Quad9
  "https://doh.mullvad.net/dns-query",       // Mullvad
];

const BOOTSTRAP_RESOLVERS = [
  "223.5.5.5",               // AliDNS
  "119.29.29.29",            // DNSPod
  "101.226.4.6",             // 360
];

const NAMESERVER_POLICY = {
  "+.tail2b5f2.ts.net": ["100.100.100.100"],  // Tailscale MagicDNS
};

function overwriteDns(config) {

  config.dns = Object.assign({}, config.dns, {
    "default-nameserver": BOOTSTRAP_RESOLVERS,
    nameserver: DIRECT_DOH,
    "proxy-server-nameserver": PROXY_DOH,
    fallback: DIRECT_DOH,
    "nameserver-policy": NAMESERVER_POLICY,

    "prefer-h3": true,
    "ipv6": false,
    "use-hosts": false,
    "use-system-hosts": false,

    // Domains excluded from the fake-ip range — must resolve to real IPs
    "fake-ip-filter": [
      "+.local",
      "+.lan",
      "+.internal",
      "+.localdomain",
      "home.arpa",
      "+.bogon",
      "+.m2m",
      "+.tail2b5f2.ts.net",
      "injections.adguard.org",
      "local.adguard.org",
      "stun.*",
      "*.stun.*",
      "*.turn.*",
      "*.srv.nintendo.net",
      "*.stun.playstation.net",
      "xbox.*.microsoft.com",
      "*.xboxlive.com",
      "lancache.steamcontent.com",
      "dns.msftncsi.com",
      "+.push.apple.com",
    ],
  });

}

// ===========================================================================
// TUN
// ===========================================================================

const TUN_OPTIONS = {
  // TUN mode itself is activated in the app GUI (requires privileged service).
  stack: "system",
  device: "tun0",
  "dns-hijack": ["any:53", "tcp://any:53"],
  "auto-route": true,
  "auto-detect-interface": true,
  "strict-route": true,
  "route-exclude-address": [],
};

function overwriteTun(config) {

  config.tun = Object.assign({}, config.tun, TUN_OPTIONS);

}

// ===========================================================================
// Proxy groups
// ===========================================================================

// Exclusion terms — nodes with these in the name are discarded (expired,
// promotional, informational, etc.)
const EXCLUDE_TERMS = "剩余|到期|主页|官网|游戏|关注|网站|地址|有效|网址|禁止|邮箱|发布|客服|订阅|节点|问题|联系";

// Country/region keywords used to classify proxy nodes
const REGIONS = {
  HK: "(香港|HK|Hong|🇭🇰)",
  TW: "(台湾|TW|Taiwan|Wan|🇹🇼|🇨🇳)",
  SG: "(新加坡|狮城|SG|Singapore|🇸🇬)",
  JP: "(日本|JP|Japan|🇯🇵)",
  KR: "(韩国|韓|KR|Korea|🇰🇷)",
  US: "(美国|🇺🇸|United\\s*States|\\bUS(\\b|[\\_\\d]))",
  UK: "(英国|UK|United Kingdom|🇬🇧)",
  FR: "(法国|FR|France|🇫🇷)",
  DE: "(德国|DE|Germany|🇩🇪)",
};

const ALL_REGIONS = Object.values(REGIONS).join("|");

// Build a regex that matches nodes for a region while excluding junk
function regionRegex(regionKey) {
  return new RegExp(
    `^(?=.*${REGIONS[regionKey]})(?!.*${EXCLUDE_TERMS}).*$`, "i"
  );
}

// Other regex — matches nodes that don't match any known region and aren't junk
const OTHER_REGEX = new RegExp(
  `^(?!.*(?:${ALL_REGIONS}|${EXCLUDE_TERMS})).*$`, "i"
);

// Filter proxy list by regex, return node names (or COMPATIBLE placeholder)
function proxiesMatching(config, regex) {
  const names = config.proxies
    .filter(function (p) { return regex.test(p.name); })
    .map(function (p) { return p.name; });
  return names.length > 0 ? names : ["COMPATIBLE"];
}

function overwriteProxyGroups(config) {

  var allProxies = config.proxies.map(function (p) { return p.name; });

  // --- Auto-select groups (one per region, url-test picks fastest) ---
  var autoGroups = [];
  var regionKeys = Object.keys(REGIONS);

  regionKeys.forEach(function (key) {
    var matched = proxiesMatching(config, regionRegex(key));
    if (matched[0] !== "COMPATIBLE") {
      autoGroups.push({
        name: key + " - 自动选择",
        type: "url-test",
        url: "https://cp.cloudflare.com",
        interval: 300,
        tolerance: 50,
        proxies: matched,
        hidden: true,
      });
    }
  });

  // Other (unmatched) nodes
  var otherProxies = proxiesMatching(config, OTHER_REGEX);
  if (otherProxies[0] !== "COMPATIBLE") {
    autoGroups.push({
      name: "其它 - 自动选择",
      type: "url-test",
      url: "https://cp.cloudflare.com",
      interval: 300,
      tolerance: 50,
      proxies: otherProxies,
      hidden: true,
    });
  }

  // --- Manual-select groups (one per region, user picks a specific node) ---
  var icons = {
    HK: "https://raw.githubusercontent.com/Orz-3/mini/master/Color/HK.png",
    JP: "https://raw.githubusercontent.com/Orz-3/mini/master/Color/JP.png",
    KR: "https://raw.githubusercontent.com/Orz-3/mini/master/Color/KR.png",
    SG: "https://raw.githubusercontent.com/Orz-3/mini/master/Color/SG.png",
    US: "https://raw.githubusercontent.com/Orz-3/mini/master/Color/US.png",
    UK: "https://raw.githubusercontent.com/Orz-3/mini/master/Color/UK.png",
    FR: "https://raw.githubusercontent.com/Orz-3/mini/master/Color/FR.png",
    DE: "https://raw.githubusercontent.com/Orz-3/mini/master/Color/DE.png",
    TW: "https://raw.githubusercontent.com/Orz-3/mini/master/Color/TW.png",
  };

  var manualGroups = [];
  regionKeys.forEach(function (key) {
    var matched = proxiesMatching(config, regionRegex(key));
    if (matched[0] !== "COMPATIBLE") {
      manualGroups.push({
        name: key + " - 手动选择",
        type: "select",
        proxies: matched,
        icon: icons[key],
        hidden: false,
      });
    }
  });

  // --- Composite groups ---

  // All auto-select group names (for use as children in select groups)
  var autoGroupNames = autoGroups.map(function (g) { return g.name; });

  // Automatic: the user selects which region to auto-route through
  var automaticProxies = ["ALL - 自动选择"].concat(autoGroupNames);

  // Manual: the user picks a region then a specific node
  var manualProxies = manualGroups.map(function (g) { return g.name; });

  // Service group proxies: node-select first, then fallback to each region
  var serviceProxies = ["🎯 节点选择"].concat(autoGroupNames);

  var groups = [
    {
      name: "🎯 节点选择",
      type: "select",
      icon: "https://raw.githubusercontent.com/Orz-3/mini/master/Color/Static.png",
      proxies: ["🔄 自动选择", "👆 手动选择", "⚖️ 负载均衡", "DIRECT"],
    },
    {
      name: "👆 手动选择",
      type: "select",
      icon: "https://raw.githubusercontent.com/Orz-3/mini/master/Color/Cylink.png",
      proxies: manualProxies,
    },
    {
      name: "🔄 自动选择",
      type: "select",
      icon: "https://raw.githubusercontent.com/Orz-3/mini/master/Color/Urltest.png",
      proxies: automaticProxies,
    },
    {
      name: "⚖️ 负载均衡",
      type: "load-balance",
      url: "https://cp.cloudflare.com",
      interval: 300,
      strategy: "consistent-hashing",
      proxies: allProxies,
      icon: "https://raw.githubusercontent.com/Orz-3/mini/master/Color/Available.png",
    },
    {
      name: "ALL - 自动选择",
      type: "url-test",
      url: "https://cp.cloudflare.com",
      interval: 300,
      tolerance: 50,
      proxies: allProxies,
      hidden: true,
    },
    {
      name: "✈️ 电报信息",
      type: "select",
      proxies: serviceProxies,
      icon: "https://raw.githubusercontent.com/Orz-3/mini/master/Color/Telegram.png",
    },
    {
      name: "🤖 AIGC",
      type: "select",
      proxies: serviceProxies,
      icon: "https://raw.githubusercontent.com/Orz-3/mini/master/Color/OpenAI.png",
    },
    {
      name: "🍎 苹果服务",
      type: "select",
      proxies: ["DIRECT"].concat(serviceProxies),
      icon: "https://raw.githubusercontent.com/Orz-3/mini/master/Color/Apple.png",
    },
    {
      name: "Ⓜ️ 微软服务",
      type: "select",
      proxies: ["DIRECT"].concat(serviceProxies),
      icon: "https://raw.githubusercontent.com/Orz-3/mini/master/Color/Microsoft.png",
    },
  ];

  // Append per-region groups
  groups = groups.concat(autoGroups);
  groups = groups.concat(manualGroups);

  config["proxy-groups"] = groups;
}

// ===========================================================================
// Rules & rule providers
// ===========================================================================

// Base rule-sets from ruleset.skk.moe (updated every 12h)
const RULE_PROVIDERS = {
  // CDN
  cdn_domainset: {
    type: "http", behavior: "domain",
    url: "https://ruleset.skk.moe/Clash/domainset/cdn.txt",
    path: "./rule_set/sukkaw_ruleset/cdn_domainset.txt",
    interval: 43200, format: "text",
  },
  cdn_non_ip: {
    type: "http", behavior: "domain",
    url: "https://ruleset.skk.moe/Clash/non_ip/cdn.txt",
    path: "./rule_set/sukkaw_ruleset/cdn_non_ip.txt",
    interval: 43200, format: "text",
  },
  // Streaming
  stream_non_ip: {
    type: "http", behavior: "classical",
    url: "https://ruleset.skk.moe/Clash/non_ip/stream.txt",
    path: "./rule_set/sukkaw_ruleset/stream_non_ip.txt",
    interval: 43200, format: "text",
  },
  stream_ip: {
    type: "http", behavior: "classical",
    url: "https://ruleset.skk.moe/Clash/ip/stream.txt",
    path: "./rule_set/sukkaw_ruleset/stream_ip.txt",
    interval: 43200, format: "text",
  },
  // AI
  ai_non_ip: {
    type: "http", behavior: "classical",
    url: "https://ruleset.skk.moe/Clash/non_ip/ai.txt",
    path: "./rule_set/sukkaw_ruleset/ai_non_ip.txt",
    interval: 43200, format: "text",
  },
  // Telegram
  telegram_non_ip: {
    type: "http", behavior: "classical",
    url: "https://ruleset.skk.moe/Clash/non_ip/telegram.txt",
    path: "./rule_set/sukkaw_ruleset/telegram_non_ip.txt",
    interval: 43200, format: "text",
  },
  telegram_ip: {
    type: "http", behavior: "classical",
    url: "https://ruleset.skk.moe/Clash/ip/telegram.txt",
    path: "./rule_set/sukkaw_ruleset/telegram_ip.txt",
    interval: 43200, format: "text",
  },
  // Apple
  apple_cdn: {
    type: "http", behavior: "domain",
    url: "https://ruleset.skk.moe/Clash/domainset/apple_cdn.txt",
    path: "./rule_set/sukkaw_ruleset/apple_cdn.txt",
    interval: 43200, format: "text",
  },
  apple_services: {
    type: "http", behavior: "classical",
    url: "https://ruleset.skk.moe/Clash/non_ip/apple_services.txt",
    path: "./rule_set/sukkaw_ruleset/apple_services.txt",
    interval: 43200, format: "text",
  },
  apple_cn_non_ip: {
    type: "http", behavior: "classical",
    url: "https://ruleset.skk.moe/Clash/non_ip/apple_cn.txt",
    path: "./rule_set/sukkaw_ruleset/apple_cn_non_ip.txt",
    interval: 43200, format: "text",
  },
  // Microsoft
  microsoft_cdn_non_ip: {
    type: "http", behavior: "classical",
    url: "https://ruleset.skk.moe/Clash/non_ip/microsoft_cdn.txt",
    path: "./rule_set/sukkaw_ruleset/microsoft_cdn_non_ip.txt",
    interval: 43200, format: "text",
  },
  microsoft_non_ip: {
    type: "http", behavior: "classical",
    url: "https://ruleset.skk.moe/Clash/non_ip/microsoft.txt",
    path: "./rule_set/sukkaw_ruleset/microsoft_non_ip.txt",
    interval: 43200, format: "text",
  },
  // Downloads
  download_domainset: {
    type: "http", behavior: "domain",
    url: "https://ruleset.skk.moe/Clash/domainset/download.txt",
    path: "./rule_set/sukkaw_ruleset/download_domainset.txt",
    interval: 43200, format: "text",
  },
  download_non_ip: {
    type: "http", behavior: "domain",
    url: "https://ruleset.skk.moe/Clash/non_ip/download.txt",
    path: "./rule_set/sukkaw_ruleset/download_non_ip.txt",
    interval: 43200, format: "text",
  },
  // LAN / domestic / direct / global
  lan_non_ip: {
    type: "http", behavior: "classical",
    url: "https://ruleset.skk.moe/Clash/non_ip/lan.txt",
    path: "./rule_set/sukkaw_ruleset/lan_non_ip.txt",
    interval: 43200, format: "text",
  },
  lan_ip: {
    type: "http", behavior: "classical",
    url: "https://ruleset.skk.moe/Clash/ip/lan.txt",
    path: "./rule_set/sukkaw_ruleset/lan_ip.txt",
    interval: 43200, format: "text",
  },
  domestic_non_ip: {
    type: "http", behavior: "classical",
    url: "https://ruleset.skk.moe/Clash/non_ip/domestic.txt",
    path: "./rule_set/sukkaw_ruleset/domestic_non_ip.txt",
    interval: 43200, format: "text",
  },
  domestic_ip: {
    type: "http", behavior: "classical",
    url: "https://ruleset.skk.moe/Clash/ip/domestic.txt",
    path: "./rule_set/sukkaw_ruleset/domestic_ip.txt",
    interval: 43200, format: "text",
  },
  direct_non_ip: {
    type: "http", behavior: "classical",
    url: "https://ruleset.skk.moe/Clash/non_ip/direct.txt",
    path: "./rule_set/sukkaw_ruleset/direct_non_ip.txt",
    interval: 43200, format: "text",
  },
  global_non_ip: {
    type: "http", behavior: "classical",
    url: "https://ruleset.skk.moe/Clash/non_ip/global.txt",
    path: "./rule_set/sukkaw_ruleset/global_non_ip.txt",
    interval: 43200, format: "text",
  },
  china_ip: {
    type: "http", behavior: "ipcidr",
    url: "https://ruleset.skk.moe/Clash/ip/china_ip.txt",
    path: "./rule_set/sukkaw_ruleset/china_ip.txt",
    interval: 43200, format: "text",
  },
};

// Custom rules (prepended before non-IP rules)
const CUSTOM_RULES = [
  "DST-PORT,22/2222/9906,DIRECT",  // SSH — always direct, no proxy
];

// Non-IP rules — checked first (domain/classical matching)
const NON_IP_RULES = [
  "RULE-SET,cdn_domainset,🎯 节点选择",
  "RULE-SET,cdn_non_ip,🎯 节点选择",
  "RULE-SET,stream_non_ip,US - 自动选择",
  "RULE-SET,telegram_non_ip,✈️ 电报信息",
  "RULE-SET,apple_cdn,DIRECT",
  "RULE-SET,download_domainset,🎯 节点选择",
  "RULE-SET,download_non_ip,🎯 节点选择",
  "RULE-SET,microsoft_cdn_non_ip,DIRECT",
  "RULE-SET,apple_cn_non_ip,DIRECT",
  "RULE-SET,apple_services,🍎 苹果服务",
  "RULE-SET,microsoft_non_ip,Ⓜ️ 微软服务",
  "RULE-SET,ai_non_ip,🤖 AIGC",
  "RULE-SET,global_non_ip,🎯 节点选择",
  "RULE-SET,domestic_non_ip,DIRECT",
  "RULE-SET,direct_non_ip,DIRECT",
  "RULE-SET,lan_non_ip,DIRECT",
];

// IP rules — checked after non-IP (IP/CIDR matching)
const IP_RULES = [
  "RULE-SET,telegram_ip,✈️ 电报信息",
  "RULE-SET,stream_ip,US - 自动选择",
  "RULE-SET,lan_ip,DIRECT",
  "RULE-SET,domestic_ip,DIRECT",
  "RULE-SET,china_ip,DIRECT",
  "MATCH,🎯 节点选择",
];

function overwriteRules(config) {

  config["rule-providers"] = RULE_PROVIDERS;

  config.rules = [].concat(
    CUSTOM_RULES,
    NON_IP_RULES,
    IP_RULES
  );

}
