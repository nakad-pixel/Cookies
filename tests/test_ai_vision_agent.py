import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.ai_vision_agent import AiVisionAgent
from src.browser_automation import CookieData, ExtractionResult
from src.vision_engines.models import ActionType, AgentAction, VisionContext


class MockVisionEngine:
    def __init__(self, actions):
        self.actions = actions
        self.index = 0

    async def analyze_screenshot(self, screenshot_b64, context):
        action = self.actions[self.index]
        self.index += 1
        return action


class TestAiVisionAgent:
    @pytest.mark.asyncio
    async def test_login_success_extracts_cookies(self):
        page = MagicMock()
        page.url = "https://example.com/dashboard"
        page.title = AsyncMock(return_value="Dashboard")
        page.content = AsyncMock(return_value="<html>Welcome</html>")
        page.screenshot = AsyncMock(return_value=b"fake_png")
        page.context = MagicMock()
        page.context.cookies = AsyncMock(return_value=[
            {"name": "session", "value": "abc", "domain": ".example.com", "secure": True, "httpOnly": True}
        ])
        page.wait_for_load_state = AsyncMock()
        page.evaluate = AsyncMock()
        page.mouse = MagicMock()
        page.mouse.move = AsyncMock()
        page.mouse.click = AsyncMock()
        page.locator.return_value = MagicMock()
        page.locator.return_value.count = AsyncMock(return_value=0)

        engine = MockVisionEngine([
            AgentAction(thought="Navigate", action=ActionType.LOGIN_SUCCESS, confidence=1.0),
        ])
        agent = AiVisionAgent(engine, max_steps=5)

        result = await agent.run_extraction(page, "test", {})
        assert result.success is True
        assert len(result.cookies) == 1
        assert result.cookies[0].name == "session"

    @pytest.mark.asyncio
    async def test_detects_2fa(self):
        page = MagicMock()
        page.url = "https://example.com/2fa"
        page.title = AsyncMock(return_value="Two-Factor Authentication")
        page.content = AsyncMock(return_value="<html>Enter code</html>")
        page.screenshot = AsyncMock(return_value=b"fake_png")
        page.wait_for_load_state = AsyncMock()
        page.evaluate = AsyncMock()
        page.mouse = MagicMock()
        page.locator.return_value = MagicMock()
        page.locator.return_value.count = AsyncMock(return_value=0)

        engine = MockVisionEngine([
            AgentAction(thought="2FA detected", action=ActionType.DETECTED_2FA, confidence=1.0),
        ])
        agent = AiVisionAgent(engine, max_steps=5)

        result = await agent.run_extraction(page, "test", {})
        assert result.has_2fa is True
        assert result.success is False

    @pytest.mark.asyncio
    async def test_detects_captcha(self):
        page = MagicMock()
        page.url = "https://example.com/captcha"
        page.title = AsyncMock(return_value="Security Check")
        page.content = AsyncMock(return_value="<html>CAPTCHA</html>")
        page.screenshot = AsyncMock(return_value=b"fake_png")
        page.wait_for_load_state = AsyncMock()
        page.evaluate = AsyncMock()
        page.locator.return_value = MagicMock()
        page.locator.return_value.count = AsyncMock(return_value=0)

        engine = MockVisionEngine([
            AgentAction(thought="CAPTCHA detected", action=ActionType.DETECTED_CAPTCHA, confidence=1.0),
        ])
        agent = AiVisionAgent(engine, max_steps=5)

        result = await agent.run_extraction(page, "test", {})
        assert result.has_captcha is True
        assert result.success is False

    @pytest.mark.asyncio
    async def test_max_steps_reached(self):
        page = MagicMock()
        page.url = "https://example.com/login"
        page.title = AsyncMock(return_value="Login")
        page.content = AsyncMock(return_value="<html>Login</html>")
        page.screenshot = AsyncMock(return_value=b"fake_png")
        page.wait_for_load_state = AsyncMock()
        page.evaluate = AsyncMock()
        page.mouse = MagicMock()
        page.locator.return_value = MagicMock()
        page.locator.return_value.count = AsyncMock(return_value=0)

        # Engine always returns WAIT — should hit max_steps
        engine = MockVisionEngine([
            AgentAction(thought="Wait", action=ActionType.WAIT, value="1", confidence=0.6),
        ] * 10)
        agent = AiVisionAgent(engine, max_steps=3)

        result = await agent.run_extraction(page, "test", {})
        assert result.success is False
        assert "Max steps" in (result.error_message or "")

    @pytest.mark.asyncio
    async def test_loop_detection(self):
        page = MagicMock()
        page.url = "https://example.com/login"
        page.title = AsyncMock(return_value="Login")
        page.content = AsyncMock(return_value="<html>Login</html>")
        page.screenshot = AsyncMock(return_value=b"fake_png")
        page.wait_for_load_state = AsyncMock()
        page.evaluate = AsyncMock()
        page.mouse = MagicMock()
        page.locator.return_value = MagicMock()
        page.locator.return_value.count = AsyncMock(return_value=0)

        # Same action repeated many times
        engine = MockVisionEngine([
            AgentAction(thought="Click login", action=ActionType.CLICK, target="#login", confidence=0.6),
        ] * 10)
        agent = AiVisionAgent(engine, max_steps=10)

        result = await agent.run_extraction(page, "test", {})
        assert result.success is False
        assert "Loop detected" in (result.error_message or "")

    @pytest.mark.asyncio
    async def test_low_confidence_becomes_wait(self):
        page = MagicMock()
        page.url = "https://example.com/login"
        page.title = AsyncMock(return_value="Login")
        page.content = AsyncMock(return_value="<html>Login</html>")
        page.screenshot = AsyncMock(return_value=b"fake_png")
        page.wait_for_load_state = AsyncMock()
        page.evaluate = AsyncMock()
        page.mouse = MagicMock()
        page.locator.return_value = MagicMock()
        page.locator.return_value.count = AsyncMock(return_value=0)

        # Low confidence action should be converted to WAIT
        engine = MockVisionEngine([
            AgentAction(thought="Unsure", action=ActionType.CLICK, target="#x", confidence=0.3),
            AgentAction(thought="Navigate", action=ActionType.LOGIN_SUCCESS, confidence=1.0),
        ])
        agent = AiVisionAgent(engine, max_steps=5)

        result = await agent.run_extraction(page, "test", {})
        # Second action is LOGIN_SUCCESS
        assert result.success is True

    @pytest.mark.asyncio
    async def test_captcha_dom_fallback(self):
        page = MagicMock()
        page.url = "https://example.com/login"
        page.title = AsyncMock(return_value="Login")
        page.content = AsyncMock(return_value="<html>Login</html>")
        page.screenshot = AsyncMock(return_value=b"fake_png")
        page.wait_for_load_state = AsyncMock()
        page.evaluate = AsyncMock()
        page.mouse = MagicMock()
        page.locator.return_value = MagicMock()
        page.locator.return_value.count = AsyncMock(return_value=1)

        # AI doesn't detect captcha, but DOM fallback does
        engine = MockVisionEngine([
            AgentAction(thought="Looks safe", action=ActionType.WAIT, value="1", confidence=0.6),
        ])
        agent = AiVisionAgent(engine, max_steps=5)

        with patch("src.ai_vision_agent.CaptchaDetector") as mock_detector_cls:
            mock_detector = MagicMock()
            mock_detector.detect_any = AsyncMock(return_value=MagicMock(present=True, type="recaptcha"))
            mock_detector_cls.return_value = mock_detector
            mock_detector_cls.detect_any = AsyncMock(return_value=MagicMock(present=True, type="recaptcha"))
            result = await agent.run_extraction(page, "test", {})
            assert result.has_captcha is True

    @pytest.mark.asyncio
    async def test_screenshot_compression(self):
        page = MagicMock()
        page.screenshot = AsyncMock(return_value=b"fake_png_data")
        page.title = AsyncMock(return_value="Login")
        page.content = AsyncMock(return_value="<html></html>")
        page.url = "https://example.com"
        page.wait_for_load_state = AsyncMock()
        page.evaluate = AsyncMock()
        page.mouse = MagicMock()
        page.locator.return_value = MagicMock()
        page.locator.return_value.count = AsyncMock(return_value=0)

        engine = MockVisionEngine([
            AgentAction(thought="Done", action=ActionType.LOGIN_SUCCESS, confidence=1.0),
        ])
        agent = AiVisionAgent(engine, max_steps=5)

        result = await agent.run_extraction(page, "test", {})
        assert result.success is True
        assert page.screenshot.called
