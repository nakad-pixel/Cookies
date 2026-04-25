import pytest
from unittest.mock import AsyncMock, MagicMock

from src.captcha_detector import CaptchaDetector, CaptchaResult


class TestCaptchaDetector:
    @pytest.mark.asyncio
    async def test_detect_recaptcha_present(self):
        """Test reCAPTCHA detection when iframe is present."""
        page = MagicMock()
        page.locator.return_value.count = AsyncMock(return_value=1)

        result = await CaptchaDetector.detect_recaptcha(page)
        assert result.present is True
        assert result.type == "recaptcha"

    @pytest.mark.asyncio
    async def test_detect_recaptcha_absent(self):
        """Test reCAPTCHA detection when nothing is present."""
        page = MagicMock()
        page.locator.return_value.count = AsyncMock(return_value=0)

        result = await CaptchaDetector.detect_recaptcha(page)
        assert result.present is False
        assert result.type == "recaptcha"

    @pytest.mark.asyncio
    async def test_detect_hcaptcha_present(self):
        """Test hCaptcha detection."""
        page = MagicMock()
        page.locator.return_value.count = AsyncMock(return_value=1)

        result = await CaptchaDetector.detect_hcaptcha(page)
        assert result.present is True
        assert result.type == "hcaptcha"

    @pytest.mark.asyncio
    async def test_detect_cloudflare_turnstile_present(self):
        """Test Cloudflare Turnstile detection."""
        page = MagicMock()
        page.locator.return_value.count = AsyncMock(return_value=1)

        result = await CaptchaDetector.detect_cloudflare_turnstile(page)
        assert result.present is True
        assert result.type == "cloudflare_turnstile"

    @pytest.mark.asyncio
    async def test_detect_js_challenge_by_title(self):
        """Test JS challenge detection by page title."""
        page = MagicMock()
        page.title = AsyncMock(return_value="Just a moment...")
        page.content = AsyncMock(return_value="<html></html>")
        page.locator.return_value.count = AsyncMock(return_value=0)

        result = await CaptchaDetector.detect_js_challenge(page)
        assert result.present is True
        assert result.type == "js_challenge"

    @pytest.mark.asyncio
    async def test_detect_js_challenge_by_content(self):
        """Test JS challenge detection by page content."""
        page = MagicMock()
        page.title = AsyncMock(return_value="Welcome")
        page.content = AsyncMock(return_value="<html>Checking your browser... Ray ID: 123</html>")
        page.locator.return_value.count = AsyncMock(return_value=0)

        result = await CaptchaDetector.detect_js_challenge(page)
        assert result.present is True
        assert result.type == "js_challenge"

    @pytest.mark.asyncio
    async def test_detect_any_returns_first_positive(self):
        """Test detect_any returns the first positive match."""
        page = MagicMock()
        page.locator.return_value.count = AsyncMock(return_value=0)
        page.title = AsyncMock(return_value="Welcome")
        page.content = AsyncMock(return_value="<html>safe</html>")

        result = await CaptchaDetector.detect_any(page)
        assert result.present is False
        assert result.type == "none"

    @pytest.mark.asyncio
    async def test_detect_any_skips_after_first_match(self):
        """Test detect_any stops after first match."""
        page = MagicMock()
        page.locator.return_value.count = AsyncMock(return_value=1)

        result = await CaptchaDetector.detect_any(page)
        assert result.present is True
        assert result.type == "recaptcha"


class TestCaptchaResult:
    def test_result_dataclass(self):
        """Test CaptchaResult dataclass."""
        result = CaptchaResult(type="recaptcha", present=True, details="iframe")
        assert result.type == "recaptcha"
        assert result.present is True
        assert result.details == "iframe"
