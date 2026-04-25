from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Dict, List

STEALTH_INIT_SCRIPTS = """
(() => {
  const _navigator = navigator;

  // navigator.webdriver
  Object.defineProperty(navigator, 'webdriver', {
    get: () => undefined,
  });

  // plugins
  const makeFakePlugins = () => {
    const plugins = [
      {name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer', description: 'Portable Document Format'},
      {name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai', description: 'Portable Document Format'},
      {name: 'Native Client', filename: 'internal-nacl-plugin', description: 'Native Client module'},
    ];
    const arr = Object.setPrototypeOf(plugins, PluginArray.prototype);
    arr.length = plugins.length;
    arr.item = idx => plugins[idx] || null;
    arr.namedItem = name => plugins.find(p => p.name === name) || null;
    arr.refresh = () => {};
    return arr;
  };

  const makeFakeMimeTypes = () => {
    const mimes = [
      {type: 'application/pdf', suffixes: 'pdf', description: 'Portable Document Format', enabledPlugin: {name: 'Chrome PDF Plugin'}},
      {type: 'application/x-google-chrome-pdf', suffixes: 'pdf', description: 'Portable Document Format', enabledPlugin: {name: 'Chrome PDF Viewer'}},
      {type: 'application/x-nacl', suffixes: '', description: 'Native Client executable', enabledPlugin: {name: 'Native Client'}},
    ];
    const arr = Object.setPrototypeOf(mimes, MimeTypeArray.prototype);
    arr.length = mimes.length;
    arr.item = idx => mimes[idx] || null;
    arr.namedItem = name => mimes.find(m => m.type === name) || null;
    return arr;
  };

  Object.defineProperty(navigator, 'plugins', {get: makeFakePlugins});
  Object.defineProperty(navigator, 'mimeTypes', {get: makeFakeMimeTypes});

  // languages
  Object.defineProperty(navigator, 'languages', {
    get: () => ['en-US', 'en'],
  });

  // hardwareConcurrency
  Object.defineProperty(navigator, 'hardwareConcurrency', {
    get: () => 8,
  });

  // chrome.runtime
  if (!window.chrome) {
    window.chrome = {};
  }
  if (!window.chrome.runtime) {
    window.chrome.runtime = {
      OnInstalledReason: {CHROME_UPDATE: 'chrome_update', UPDATE: 'update', INSTALL: 'install'},
      OnRestartRequiredReason: {APP_UPDATE: 'app_update', OS_UPDATE: 'os_update', PERIODIC: 'periodic'},
      PlatformArch: {ARM: 'arm', ARM64: 'arm64', MIPS: 'mips', MIPS64: 'mips64', MIPS64EL: 'mips64el', X86_32: 'x86-32', X86_64: 'x86-64'},
      PlatformNaclArch: {ARM: 'arm', MIPS: 'mips', MIPS64: 'mips64', MIPS64EL: 'mips64el', X86_32: 'x86-32', X86_64: 'x86-64'},
      PlatformOs: {ANDROID: 'android', CROS: 'cros', LINUX: 'linux', MAC: 'mac', OPENBSD: 'openbsd', WIN: 'win'},
      RequestUpdateCheckStatus: {NO_UPDATE: 'no_update', THROTTLED: 'throttled', UPDATE_AVAILABLE: 'update_available'},
    };
  }

  // Notification.permission
  Object.defineProperty(Notification, 'permission', {
    get: () => 'default',
  });

  // Permissions.prototype.query
  const originalQuery = window.Permissions.prototype.query;
  window.Permissions.prototype.query = async function(args) {
    if (args && args.name && args.name === 'notifications') {
      return {state: 'prompt', onchange: null};
    }
    return originalQuery.call(this, args);
  };

  // WebGL spoofing
  const getParameterProxyHandler = {
    apply: function(target, thisArg, args) {
      if (args[0] === 37445) {
        return 'Intel Inc.';
      }
      if (args[0] === 37446) {
        return 'Intel Iris OpenGL Engine';
      }
      return target.apply(thisArg, args);
    }
  };

  const getParameter = WebGLRenderingContext.prototype.getParameter;
  WebGLRenderingContext.prototype.getParameter = new Proxy(getParameter, getParameterProxyHandler);

  // Canvas noise
  const originalGetImageData = CanvasRenderingContext2D.prototype.getImageData;
  CanvasRenderingContext2D.prototype.getImageData = function(...args) {
    const imageData = originalGetImageData.apply(this, args);
    const data = imageData.data;
    for (let i = 0; i < data.length; i += 4) {
      data[i] += (Math.random() < 0.5 ? -1 : 1);
    }
    return imageData;
  };

  // outerWidth / outerHeight
  Object.defineProperty(window, 'outerWidth', {
    get: () => window.innerWidth,
  });
  Object.defineProperty(window, 'outerHeight', {
    get: () => window.innerHeight,
  });
})();
"""

STEALTH_LAUNCH_ARGS: List[str] = [
    "--disable-blink-features=AutomationControlled",
    "--disable-features=IsolateOrigins,site-per-process",
    "--disable-site-isolation-trials",
    "--disable-web-security",
    "--disable-features=BlockInsecurePrivateNetworkRequests",
    "--no-sandbox",
    "--disable-setuid-sandbox",
    "--disable-dev-shm-usage",
    "--disable-accelerated-2d-canvas",
    "--disable-gpu",
    "--window-size=1920,1080",
    "--start-maximized",
    "--disable-background-networking",
    "--disable-background-timer-throttling",
    "--disable-backgrounding-occluded-windows",
    "--disable-breakpad",
    "--disable-component-extensions-with-background-pages",
    "--disable-default-apps",
    "--disable-extensions",
    "--disable-features=TranslateUI",
    "--disable-hang-monitor",
    "--disable-ipc-flooding-protection",
    "--disable-popup-blocking",
    "--disable-prompt-on-repost",
    "--disable-renderer-backgrounding",
    "--force-color-profile=srgb",
    "--metrics-recording-only",
    "--password-store=basic",
    "--use-mock-keychain",
]


@dataclass
class Fingerprint:
    viewport: Dict[str, int]
    user_agent: str
    locale: str
    timezone: str
    hardware_concurrency: int
    webgl_vendor: str
    webgl_renderer: str
    color_scheme: str


VIEWPORTS = [
    {"width": 1920, "height": 1080},
    {"width": 1366, "height": 768},
    {"width": 1440, "height": 900},
    {"width": 1536, "height": 864},
    {"width": 1280, "height": 720},
]

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
]

LOCALES = ["en-US", "en-GB", "de-DE", "fr-FR", "es-ES", "ja-JP"]
TIMEZONES = [
    "America/New_York",
    "America/Chicago",
    "America/Los_Angeles",
    "Europe/London",
    "Europe/Berlin",
    "Europe/Paris",
    "Asia/Tokyo",
    "Australia/Sydney",
]
WEBGL_PROFILES = [
    {"vendor": "Intel Inc.", "renderer": "Intel Iris OpenGL Engine"},
    {"vendor": "Google Inc. (NVIDIA)", "renderer": "ANGLE (NVIDIA, NVIDIA GeForce GTX 1660 Direct3D11 vs_5_0 ps_5_0, D3D11)"},
    {"vendor": "Apple Inc.", "renderer": "Apple M1"},
]

HARDWARE_CONCURRENCY_OPTIONS = [4, 8, 16]


class FingerprintPool:
    """Generate randomized but consistent fingerprints per platform."""

    def __init__(self, seed: int | None = None) -> None:
        self._rng = random.Random(seed)
        self._cache: Dict[str, Fingerprint] = {}

    def get_fingerprint(self, platform: str) -> Fingerprint:
        """Return a randomized but consistent fingerprint for a platform."""
        if platform in self._cache:
            return self._cache[platform]
        fp = self._generate()
        self._cache[platform] = fp
        return fp

    def _generate(self) -> Fingerprint:
        viewport = self._rng.choice(VIEWPORTS)
        ua = self._rng.choice(USER_AGENTS)
        locale = self._rng.choice(LOCALES)
        tz = self._rng.choice(TIMEZONES)
        hw = self._rng.choice(HARDWARE_CONCURRENCY_OPTIONS)
        webgl = self._rng.choice(WEBGL_PROFILES)
        color = self._rng.choice(["light", "dark"])
        return Fingerprint(
            viewport=viewport,
            user_agent=ua,
            locale=locale,
            timezone=tz,
            hardware_concurrency=hw,
            webgl_vendor=webgl["vendor"],
            webgl_renderer=webgl["renderer"],
            color_scheme=color,
        )


def get_fingerprint(platform: str, seed: int | None = None) -> Fingerprint:
    """Get a fingerprint for a platform."""
    pool = FingerprintPool(seed=seed)
    return pool.get_fingerprint(platform)
