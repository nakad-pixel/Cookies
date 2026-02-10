import importlib

import pytest

import src.browser_automation as browser_automation


def test_browser_automation_missing_playwright(monkeypatch) -> None:
    monkeypatch.setattr(browser_automation, "sync_playwright", None)
    automation = browser_automation.BrowserAutomation()
    with pytest.raises(RuntimeError):
        automation.extract_cookies("https://example.com")
