from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class HeaderProfile:
    accept: str
    accept_language: str
    accept_encoding: str
    sec_ch_ua: str
    sec_ch_ua_mobile: str
    sec_ch_ua_platform: str
    upgrade_insecure_requests: str
    dnt: str


CHROMIUM_VERSIONS = [
    '"Chromium";v="124", "Not-A.Brand";v="99"',
    '"Google Chrome";v="124", "Chromium";v="124", "Not-A.Brand";v="99"',
    '"HeadlessChrome";v="124", "Chromium";v="124", "Not-A.Brand";v="99"',
]

PLATFORMS = ["Windows", "macOS", "Linux"]


class HeaderFingerprinter:
    """Generate randomized but realistic request headers per platform."""

    def __init__(self, seed: int | None = None) -> None:
        self._rng = random.Random(seed)
        self._cache: Dict[str, Dict[str, str]] = {}

    def get_random_headers(self, platform: str = "generic") -> Dict[str, str]:
        """Return randomized realistic headers for a platform.

        Args:
            platform: Platform name used for locale matching.

        Returns:
            Dictionary of HTTP headers.
        """
        if platform in self._cache:
            return self._cache[platform]

        locale = self._locale_for_platform(platform)
        sec_ch_ua = self._rng.choice(CHROMIUM_VERSIONS)
        platform_val = self._rng.choice(PLATFORMS)

        headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": locale,
            "Accept-Encoding": "gzip, deflate, br",
            "Sec-Ch-Ua": sec_ch_ua,
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": f'"{platform_val}"',
            "Upgrade-Insecure-Requests": "1",
            "DNT": "1",
        }
        self._cache[platform] = headers
        return headers

    @staticmethod
    def _locale_for_platform(platform: str) -> str:
        mapping = {
            "github": "en-US,en;q=0.9",
            "gitlab": "en-US,en;q=0.9",
            "google": "en-US,en;q=0.9",
            "aws": "en-US,en;q=0.9",
            "azure": "en-US,en;q=0.9",
        }
        return mapping.get(platform.lower(), "en-US,en;q=0.9")
