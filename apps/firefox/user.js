// Firefox user.js — managed by dotfiles
// Sources: arkenfox user.js v144 (2026-04-21) + custom settings
// Add settings here and run install.py to apply.

// -- 0000: disable about:config warning --------------------------------------
user_pref("browser.aboutConfig.showWarning", false);

// -- 0100: startup pages (Firefox Home, no sponsored content) ---------------
user_pref("browser.startup.page", 3);      // restore previous session
user_pref("browser.startup.homepage", "about:home");
user_pref("browser.warnOnQuit", true);     // warn before closing multiple tabs
// Block sponsored content on Firefox Home
user_pref("browser.newtabpage.activity-stream.showSponsored", false);
user_pref("browser.newtabpage.activity-stream.showSponsoredTopSites", false);
user_pref("browser.newtabpage.activity-stream.showSponsoredCheckboxes", false);
// Clear the default top sites (you'll add your own)
user_pref("browser.newtabpage.activity-stream.default.sites", "");

// -- 0200: disable OS geolocation services -----------------------------------
user_pref("geo.provider.ms-windows-location", false);                // [WINDOWS]
user_pref("geo.provider.use_corelocation", false);                   // [MAC]
user_pref("geo.provider.use_geoclue", false);                        // [LINUX]

// -- 0300: disable recommendations and reports -------------------------------
// Extension recommendations
user_pref("extensions.getAddons.showPane", false);                   // [HIDDEN PREF]
user_pref("extensions.htmlaboutaddons.recommendations.enabled", false);
user_pref("browser.discovery.enabled", false);
// Telemetry
user_pref("browser.newtabpage.activity-stream.feeds.telemetry", false);
user_pref("browser.newtabpage.activity-stream.telemetry", false);
// Studies / Normandy
user_pref("app.shield.optoutstudies.enabled", false);
user_pref("app.normandy.enabled", false);
user_pref("app.normandy.api_url", "");
// Crash reports
user_pref("breakpad.reportURL", "");
user_pref("browser.tabs.crashReporting.sendReport", false);
user_pref("browser.crashReports.unsubmittedCheck.autoSubmit2", false);
// Network probes
user_pref("captivedetect.canonicalURL", "");
user_pref("network.captive-portal-service.enabled", false);
user_pref("network.connectivity-service.enabled", false);

// -- 0400: Safe Browsing -----------------------------------------------------
// Keep SB itself enabled (0401/0402). Only disable remote download hash upload.
user_pref("browser.safebrowsing.downloads.remote.enabled", false);

// -- 0600: block implicit outbound (speculative connections) -----------------
user_pref("network.prefetch-next", false);                           // link prefetching
user_pref("network.dns.disablePrefetchFromHTTPS", true);             // DNS via HTTPS docs
user_pref("network.http.speculative-parallel-limit", 0);             // mouseover preconnect
user_pref("browser.places.speculativeConnect.enabled", false);       // bookmark preconnect

// -- 0800: location bar / search / suggestions -------------------------------
// Speculative connections while typing in the URL bar
user_pref("browser.urlbar.speculativeConnect.enabled", false);
// Firefox Suggest (Mozilla's ad platform in the URL bar)
user_pref("browser.urlbar.quicksuggest.enabled", false);
user_pref("browser.urlbar.suggest.quicksuggest.nonsponsored", false);
user_pref("browser.urlbar.suggest.quicksuggest.sponsored", false);
// Live search suggestions (sends keystrokes to search engine)
user_pref("browser.search.suggest.enabled", false);
user_pref("browser.urlbar.suggest.searches", false);
// Trending search suggestions
user_pref("browser.urlbar.trending.featureGate", false);
// Misc urlbar feature gates (weather, yelp, wikipedia, ads, etc.)
user_pref("browser.urlbar.addons.featureGate", false);
user_pref("browser.urlbar.amp.featureGate", false);
user_pref("browser.urlbar.importantDates.featureGate", false);
user_pref("browser.urlbar.market.featureGate", false);
user_pref("browser.urlbar.mdn.featureGate", false);
user_pref("browser.urlbar.weather.featureGate", false);
user_pref("browser.urlbar.wikipedia.featureGate", false);
user_pref("browser.urlbar.yelp.featureGate", false);
user_pref("browser.urlbar.yelpRealtime.featureGate", false);
// Form and search history
user_pref("browser.formfill.enable", false);
// Separate search engine for Private Windows
user_pref("browser.search.separatePrivateDefault", true);
user_pref("browser.search.separatePrivateDefault.ui.enabled", true);

// -- 0900: passwords (Bitwarden handles this — Firefox shouldn't) -----------
user_pref("signon.autofillForms", false);                // don't auto-fill passwords
user_pref("signon.formlessCapture.enabled", false);      // don't prompt to save passwords
// Limit HTTP auth dialogs to same-origin (anti-phishing)
user_pref("network.auth.subresource-http-auth-allow", 1);

// -- 1000: disk avoidance (keep data in memory, not on disk) ----------------
user_pref("browser.cache.disk.enable", false);
user_pref("browser.privatebrowsing.forceMediaMemoryCache", true);
user_pref("media.memory_cache_max_size", 65536);
// Don't save form content, cookies, POST data for session restore
user_pref("browser.sessionstore.privacy_level", 2);
user_pref("toolkit.winRegisterApplicationRestart", false);        // [WINDOWS]
user_pref("browser.shell.shortcutFavicons", false);               // [WINDOWS]

// -- 1200: HTTPS (TLS / certs / mixed content) ------------------------------
// Require safe TLS renegotiation (99.85% of sites support this)
user_pref("security.ssl.require_safe_negotiation", true);
// Disable TLS 1.3 0-RTT (not forward secret, replayable)
user_pref("security.tls.enable_0rtt_data", false);
// Strict public key pinning — no MiTM override
user_pref("security.cert_pinning.enforcement_level", 2);
// HTTPS-Only mode in all windows
user_pref("dom.security.https_only_mode", true);
// Don't send plaintext HTTP probe when HTTPS upgrade fails
user_pref("dom.security.https_only_mode_send_http_background_request", false);
// Show broken padlock for unsafe negotiation
user_pref("security.ssl.treat_unsafe_negotiation_as_broken", true);
// Show details on certificate error pages
user_pref("browser.xul.error_pages.expert_bad_cert", true);

// -- 1600: referers ----------------------------------------------------------
// Cross-origin: only send scheme+host+port (not full URL path)
user_pref("network.http.referer.XOriginTrimmingPolicy", 2);

// -- 1700: containers --------------------------------------------------------
user_pref("privacy.userContext.enabled", true);
user_pref("privacy.userContext.ui.enabled", true);

// -- 2000: WebRTC ------------------------------------------------------------
// Disable WebRTC entirely — prevents local IP leaks. WebRTC is only needed
// for browser-based voice/video calls (Google Meet, Discord Web, Zoom Web).
// Native apps (FaceTime, Zoom, Slack desktop) are unaffected.
user_pref("media.peerconnection.enabled", false);

// -- 2400: DOM ----------------------------------------------------------------
// Prevent scripts from moving/resizing windows
user_pref("dom.disable_window_move_resize", true);

// -- 2600: miscellaneous ----------------------------------------------------
// Temp files: start in tmp dir, delete on exit
user_pref("browser.download.start_downloads_in_tmp_dir", true);
user_pref("browser.helperApps.deleteTempFileOnExit", true);
// Disable UITour (remote page onboarding)
user_pref("browser.uitour.enabled", false);
// Remove special permissions for Mozilla domains
user_pref("permissions.manager.defaultsUrl", "");
// Show punycode to prevent homograph phishing attacks
user_pref("network.IDN_show_punycode", true);
// Disable JavaScript execution in PDFs
user_pref("pdfjs.enableScripting", false);
// Isolate content script resources from extensions
user_pref("privacy.antitracking.isolateContentScriptResources", true);
// Disable CSP reporting (can leak URLs to third parties)
user_pref("security.csp.reporting.enabled", false);
// Don't add downloads to system's recent documents list
user_pref("browser.download.manager.addToRecentDocs", false);
// Ask before handling unfamiliar file types
user_pref("browser.download.always_ask_before_handling_new_types", true);
// Limit extension directories to profile + application
user_pref("extensions.enabledScopes", 5);
// Don't bypass third-party extension install warnings
user_pref("extensions.postDownloadThirdPartyPrompt", false);

// -- 2700: ETP (Enhanced Tracking Protection) --------------------------------
// Strict mode: Total Cookie Protection (isolates every site's cookies)
user_pref("browser.contentblocking.category", "strict");

// -- 2800: manual sanitize defaults (Ctrl-Shift-Del / Clear Data dialogs) ----
// These don't run automatically — they preset checkboxes for manual clearing.
user_pref("privacy.clearSiteData.cache", true);
user_pref("privacy.clearSiteData.cookiesAndStorage", false);
user_pref("privacy.clearSiteData.historyFormDataAndDownloads", false);
user_pref("privacy.clearSiteData.browsingHistoryAndDownloads", false);
user_pref("privacy.clearSiteData.formdata", true);
user_pref("privacy.clearHistory.cache", true);
user_pref("privacy.clearHistory.cookiesAndStorage", false);
user_pref("privacy.clearHistory.historyFormDataAndDownloads", false);
user_pref("privacy.clearHistory.browsingHistoryAndDownloads", false);
user_pref("privacy.clearHistory.formdata", true);
// Default time range to "Everything" in manual clear dialogs
user_pref("privacy.sanitize.timeSpan", 0);

// -- 4500: RFP-adjacent (without enabling full RFP) --------------------------
// Block mozAddonManager API (fingerprinting vector)
user_pref("privacy.resistFingerprinting.block_mozAddonManager", true);
// Suppress "Request English versions" prompt
user_pref("privacy.spoof_english", 1);
// Don't leak system accent colors
user_pref("widget.non-native-theme.use-theme-accent", false);
// Force all window.open calls into tabs (prevents screen-size leaks)
user_pref("browser.link.open_newwindow.restriction", 0);

// -- 8500: telemetry (core infrastructure) ----------------------------------
user_pref("datareporting.policy.dataSubmissionEnabled", false);
user_pref("datareporting.healthreport.uploadEnabled", false);
user_pref("toolkit.telemetry.unified", false);
user_pref("toolkit.telemetry.enabled", false);
user_pref("toolkit.telemetry.server", "data:,");
user_pref("toolkit.telemetry.archive.enabled", false);
user_pref("toolkit.telemetry.newProfilePing.enabled", false);
user_pref("toolkit.telemetry.shutdownPingSender.enabled", false);
user_pref("toolkit.telemetry.updatePing.enabled", false);
user_pref("toolkit.telemetry.bhrPing.enabled", false);
user_pref("toolkit.telemetry.firstShutdownPing.enabled", false);
user_pref("toolkit.telemetry.coverage.opt-out", true);
user_pref("toolkit.coverage.opt-out", true);
user_pref("toolkit.coverage.endpoint.base", "");

// -- 9000: non-project (annoyance prevention) -------------------------------
// Disable "Recommended extensions/features" popups
user_pref("browser.newtabpage.activity-stream.asrouter.userprefs.cfr.addons", false);
user_pref("browser.newtabpage.activity-stream.asrouter.userprefs.cfr.features", false);
// Show actual URL instead of search terms in the address bar
user_pref("browser.urlbar.showSearchTerms.enabled", false);

// -- DNS --------------------------------------------------------------------
// Let Clash handle DNS. Disable Firefox's own DoH and DNS prefetching.
user_pref("network.trr.mode", 5);
user_pref("network.dns.disablePrefetch", true);

// -- Search -----------------------------------------------------------------
// Use DuckDuckGo as the default search engine
user_pref("browser.search.defaultenginename", "DuckDuckGo");
user_pref("browser.search.selectedEngine", "DuckDuckGo");
