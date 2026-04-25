import pytest
from unittest.mock import AsyncMock, MagicMock, patch

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


class TestBrowserAutomationAsync:
    @pytest.mark.asyncio
    async def test_extract_cookies_raises_without_patchright(self, monkeypatch):
        """Test that extract_cookies raises when patchright is not installed."""
        monkeypatch.setattr(browser_automation, "async_playwright", None)
        automation = BrowserAutomation()
        with pytest.raises(RuntimeError, match="patchright is not installed"):
            await automation.extract_cookies("https://example.com")

    @pytest.mark.asyncio
    async def test_extract_cookies_success_no_login(self, monkeypatch):
        """Test successful cookie extraction without credentials."""
        automation = BrowserAutomation()

        mock_pw = MagicMock()
        mock_browser = MagicMock()
        mock_context = MagicMock()
        mock_page = MagicMock()

        mock_context.cookies = AsyncMock(return_value=[
            {"name": "session", "value": "abc", "domain": ".example.com", "secure": True, "httpOnly": True}
        ])
        mock_context.new_page = AsyncMock(return_value=mock_page)
        mock_context.add_init_script = AsyncMock(return_value=None)
        mock_context.close = AsyncMock()
        mock_context.tracing = MagicMock()
        mock_context.tracing.start = AsyncMock()
        mock_context.tracing.stop = AsyncMock()

        mock_browser.new_context = AsyncMock(return_value=mock_context)
        mock_pw.chromium = MagicMock()
        mock_pw.chromium.launch = AsyncMock(return_value=mock_browser)
        mock_pw.start = AsyncMock(return_value=mock_pw)
        mock_pw.stop = AsyncMock()

        monkeypatch.setattr(browser_automation, "async_playwright", lambda: mock_pw)
        monkeypatch.setattr(
            browser_automation,
            "get_fingerprint",
            lambda platform: MagicMock(
                viewport={"width": 1920, "height": 1080},
                user_agent="Mozilla/5.0",
                locale="en-US",
                timezone="UTC",
                color_scheme="light",
            ),
        )
        monkeypatch.setattr(
            browser_automation,
            "CaptchaDetector",
            MagicMock(detect_any=AsyncMock(return_value=MagicMock(present=False))),
        )

        result = await automation.extract_cookies("https://example.com", platform="github")

        assert result.success is True
        assert len(result.cookies) == 1
        assert result.cookies[0].name == "session"

    @pytest.mark.asyncio
    async def test_extract_cookies_detects_2fa(self, monkeypatch):
        """Test that extraction detects 2FA and returns has_2fa=True."""
        automation = BrowserAutomation()

        mock_pw = MagicMock()
        mock_browser = MagicMock()
        mock_context = MagicMock()
        mock_page = MagicMock()

        mock_page.content = AsyncMock(return_value="<html>two-factor authentication required</html>")
        mock_page.title = AsyncMock(return_value="Login")
        mock_page.set_extra_http_headers = AsyncMock()
        mock_page.goto = AsyncMock()
        mock_page.evaluate = AsyncMock(return_value={"x": 0, "y": 0})
        mock_page.mouse = MagicMock()
        mock_page.mouse.move = AsyncMock()

        mock_context.new_page = AsyncMock(return_value=mock_page)
        mock_context.add_init_script = AsyncMock()
        mock_context.cookies = AsyncMock(return_value=[])
        mock_context.close = AsyncMock()

        mock_browser.new_context = AsyncMock(return_value=mock_context)
        mock_pw.chromium = MagicMock()
        mock_pw.chromium.launch = AsyncMock(return_value=mock_browser)
        mock_pw.start = AsyncMock(return_value=mock_pw)
        mock_pw.stop = AsyncMock()

        monkeypatch.setattr(browser_automation, "async_playwright", lambda: mock_pw)
        monkeypatch.setattr(
            browser_automation,
            "get_fingerprint",
            lambda platform: MagicMock(
                viewport={"width": 1920, "height": 1080},
                user_agent="Mozilla/5.0",
                locale="en-US",
                timezone="UTC",
                color_scheme="light",
            ),
        )
        monkeypatch.setattr(
            browser_automation,
            "CaptchaDetector",
            MagicMock(detect_any=AsyncMock(return_value=MagicMock(present=False))),
        )
        monkeypatch.setattr(
            browser_automation,
            "emulate_scroll",
            AsyncMock(),
        )
        monkeypatch.setattr(
            browser_automation,
            "random_human_wait",
            AsyncMock(),
        )

        result = await automation.extract_cookies("https://example.com", platform="github")

        assert result.has_2fa is True
        assert result.success is False

    @pytest.mark.asyncio
    async def test_validate_cookies_success(self, monkeypatch):
        """Test cookie validation."""
        automation = BrowserAutomation()

        mock_pw = MagicMock()
        mock_browser = MagicMock()
        mock_context = MagicMock()
        mock_page = MagicMock()

        mock_response = MagicMock()
        mock_response.ok = True
        mock_page.goto = AsyncMock(return_value=mock_response)

        mock_context.new_page = AsyncMock(return_value=mock_page)
        mock_context.add_cookies = AsyncMock()
        mock_context.close = AsyncMock()
        mock_browser.new_context = AsyncMock(return_value=mock_context)
        mock_pw.chromium = MagicMock()
        mock_pw.chromium.launch = AsyncMock(return_value=mock_browser)
        mock_pw.start = AsyncMock(return_value=mock_pw)
        mock_pw.stop = AsyncMock()

        monkeypatch.setattr(browser_automation, "async_playwright", lambda: mock_pw)
        monkeypatch.setattr(
            browser_automation,
            "get_fingerprint",
            lambda platform: MagicMock(
                viewport={"width": 1920, "height": 1080},
                user_agent="Mozilla/5.0",
                locale="en-US",
                timezone="UTC",
                color_scheme="light",
            ),
        )

        cookies = [CookieData(name="session", value="abc", domain=".example.com")]
        valid = await automation.validate_cookies("https://example.com", cookies)

        assert valid is True


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
