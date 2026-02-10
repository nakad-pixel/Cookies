import pytest

import src.browser_automation as browser_automation
from src.browser_automation import (
    BrowserAutomation,
    CookieData,
    ExtractionResult,
    TwoFactorAuthError,
)


class TestCookieData:
    def test_cookie_data_creation(self):
        """Test CookieData dataclass creation."""
        cookie = CookieData(
            name="session_id",
            value="abc123",
            domain=".example.com",
            expires=1234567890,
            secure=True,
            http_only=True,
        )
        assert cookie.name == "session_id"
        assert cookie.value == "abc123"
        assert cookie.domain == ".example.com"

    def test_cookie_wipe_clears_value(self):
        """Test that wipe() clears the cookie value."""
        cookie = CookieData(
            name="session_id",
            value="sensitive-secret-value",
            domain=".example.com",
        )
        cookie.wipe()
        assert cookie.value == ""


class TestExtractionResult:
    def test_extraction_result_creation(self):
        """Test ExtractionResult creation."""
        result = ExtractionResult(
            cookies=[CookieData(name="test", value="val", domain=".test.com")],
            has_2fa=False,
            success=True,
        )
        assert len(result.cookies) == 1
        assert result.has_2fa is False
        assert result.success is True

    def test_wipe_cookies_clears_all(self):
        """Test that wipe_cookies clears all cookie values."""
        result = ExtractionResult(
            cookies=[
                CookieData(name="c1", value="secret1", domain=".test.com"),
                CookieData(name="c2", value="secret2", domain=".test.com"),
            ],
            success=True,
        )
        result.wipe_cookies()
        assert len(result.cookies) == 0


class TestBrowserAutomationMissingPlaywright:
    def test_extract_cookies_raises_without_playwright(self, monkeypatch):
        """Test that extract_cookies raises when playwright is not installed."""
        monkeypatch.setattr(browser_automation, "sync_playwright", None)
        automation = BrowserAutomation()
        with pytest.raises(RuntimeError, match="Playwright is not installed"):
            automation.extract_cookies("https://example.com")

    def test_validate_cookies_raises_without_playwright(self, monkeypatch):
        """Test that validate_cookies raises when playwright is not installed."""
        monkeypatch.setattr(browser_automation, "sync_playwright", None)
        automation = BrowserAutomation()
        cookies = [CookieData(name="test", value="val", domain=".test.com")]
        with pytest.raises(RuntimeError, match="Playwright is not installed"):
            automation.validate_cookies("https://example.com", cookies)


class TestTwoFactorDetection:
    def test_2fa_patterns_defined(self):
        """Test that 2FA detection patterns are defined."""
        automation = BrowserAutomation()
        assert len(automation.TWO_FA_PATTERNS) > 0
        assert "two-factor" in automation.TWO_FA_PATTERNS
        assert "2fa" in automation.TWO_FA_PATTERNS
        assert "authenticator" in automation.TWO_FA_PATTERNS

    def test_2fa_selectors_defined(self):
        """Test that 2FA selectors are defined."""
        automation = BrowserAutomation()
        assert len(automation.TWO_FA_SELECTORS) > 0
        assert any("2fa" in s for s in automation.TWO_FA_SELECTORS)
        assert any("code" in s for s in automation.TWO_FA_SELECTORS)


class TestTwoFactorAuthError:
    def test_error_is_exception(self):
        """Test that TwoFactorAuthError is an exception."""
        with pytest.raises(TwoFactorAuthError):
            raise TwoFactorAuthError("2FA required")


class TestUserAgent:
    def test_random_user_agent_returned(self):
        """Test that a user agent string is returned."""
        automation = BrowserAutomation()
        ua = automation._get_random_user_agent()
        assert isinstance(ua, str)
        assert "Mozilla" in ua
        assert len(ua) > 50
