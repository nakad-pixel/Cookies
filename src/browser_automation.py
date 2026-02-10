from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Dict, List

try:
    from playwright.sync_api import sync_playwright
except ImportError:  # pragma: no cover - optional dependency
    sync_playwright = None


@dataclass
class CookieData:
    name: str
    value: str
    domain: str
    expires: int | None


class BrowserAutomation:
    def __init__(self, headless: bool = True) -> None:
        self.headless = headless

    def extract_cookies(self, url: str) -> List[CookieData]:
        if sync_playwright is None:
            raise RuntimeError("Playwright is not installed")
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=self.headless)
            context = browser.new_context(
                viewport={"width": random.choice([1280, 1366, 1440]), "height": random.choice([720, 768, 900])},
                timezone_id=random.choice(["UTC", "America/New_York", "Europe/London"]),
            )
            page = context.new_page()
            page.goto(url, wait_until="networkidle")
            cookies = context.cookies()
            browser.close()
        return [
            CookieData(
                name=cookie["name"],
                value=cookie["value"],
                domain=cookie.get("domain", ""),
                expires=cookie.get("expires"),
            )
            for cookie in cookies
        ]

    def validate_cookies(self, url: str, cookies: List[CookieData]) -> bool:
        if sync_playwright is None:
            raise RuntimeError("Playwright is not installed")
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=self.headless)
            context = browser.new_context()
            context.add_cookies(
                [
                    {
                        "name": cookie.name,
                        "value": cookie.value,
                        "domain": cookie.domain,
                        "path": "/",
                    }
                    for cookie in cookies
                ]
            )
            page = context.new_page()
            response = page.goto(url, wait_until="domcontentloaded")
            browser.close()
        return bool(response) and response.ok
