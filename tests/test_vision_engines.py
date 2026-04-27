import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.vision_engines.base import VisionEngine
from src.vision_engines.models import ActionType, AgentAction, VisionContext
from src.vision_engines.rule_engine import RuleBasedVisionEngine


class TestActionType:
    def test_enum_values(self):
        assert ActionType.CLICK.value == "CLICK"
        assert ActionType.TYPE.value == "TYPE"
        assert ActionType.LOGIN_SUCCESS.value == "LOGIN_SUCCESS"
        assert ActionType.ERROR.value == "ERROR"


class TestAgentAction:
    def test_to_dict(self):
        action = AgentAction(
            thought="Click login button",
            action=ActionType.CLICK,
            target="#login",
            confidence=0.9,
        )
        d = action.to_dict()
        assert d["action"] == "CLICK"
        assert d["target"] == "#login"
        assert d["confidence"] == 0.9

    def test_from_dict(self):
        d = {
            "thought": "Type password",
            "action": "TYPE",
            "target": "#password",
            "value": "secret",
            "confidence": 0.8,
        }
        action = AgentAction.from_dict(d)
        assert action.action == ActionType.TYPE
        assert action.target == "#password"
        assert action.value == "secret"

    def test_from_dict_invalid_action(self):
        d = {"thought": "Unknown", "action": "UNKNOWN_ACTION"}
        action = AgentAction.from_dict(d)
        assert action.action == ActionType.ERROR


class TestVisionContext:
    def test_creation(self):
        ctx = VisionContext(
            url="https://example.com/login",
            goal="Log in",
            platform="test",
        )
        assert ctx.url == "https://example.com/login"
        assert ctx.platform == "test"


class TestRuleBasedVisionEngine:
    @pytest.mark.asyncio
    async def test_detects_2fa_from_content(self):
        engine = RuleBasedVisionEngine()
        ctx = VisionContext(
            url="https://example.com",
            goal="Login",
            platform="test",
            history=[{"page_content": "Please enter your two-factor authentication code", "page_title": "2FA"}],
        )
        action = await engine.analyze_screenshot("", ctx)
        assert action.action == ActionType.DETECTED_2FA

    @pytest.mark.asyncio
    async def test_detects_captcha_from_content(self):
        engine = RuleBasedVisionEngine()
        ctx = VisionContext(
            url="https://example.com",
            goal="Login",
            platform="test",
            history=[{"page_content": "Please solve the captcha", "page_title": "Security Check"}],
        )
        action = await engine.analyze_screenshot("", ctx)
        assert action.action == ActionType.DETECTED_CAPTCHA

    @pytest.mark.asyncio
    async def test_waits_when_no_info(self):
        engine = RuleBasedVisionEngine()
        ctx = VisionContext(
            url="https://example.com",
            goal="Login",
            platform="test",
            history=[],
        )
        action = await engine.analyze_screenshot("", ctx)
        assert action.action == ActionType.WAIT

    @pytest.mark.asyncio
    async def test_login_success_indicators(self):
        engine = RuleBasedVisionEngine()
        ctx = VisionContext(
            url="https://example.com/dashboard",
            goal="Login",
            platform="test",
            history=[{"page_content": "Welcome to your dashboard logout", "page_title": "Dashboard"}],
        )
        action = await engine.analyze_screenshot("", ctx)
        assert action.action == ActionType.LOGIN_SUCCESS

    @pytest.mark.asyncio
    async def test_suggests_type_username(self):
        engine = RuleBasedVisionEngine()
        ctx = VisionContext(
            url="https://example.com/login",
            goal="Login",
            platform="test",
            history=[{"page_content": 'input name="username"', "page_title": "Login"}],
        )
        action = await engine.analyze_screenshot("", ctx)
        assert action.action == ActionType.TYPE
        assert "username" in action.target.lower() or "login" in action.target.lower()


class TestGeminiVisionEngine:
    @pytest.mark.asyncio
    async def test_initialization_fails_without_key(self):
        with pytest.raises(RuntimeError):
            from src.vision_engines.gemini_engine import GeminiVisionEngine
            GeminiVisionEngine(api_key="")

    @pytest.mark.asyncio
    async def test_parse_response_valid_json(self):
        from src.vision_engines.gemini_engine import GeminiVisionEngine
        engine = GeminiVisionEngine(api_key="fake-key")
        action = engine._parse_response('{"thought":"ok","action":"CLICK","target":"#btn","confidence":0.9}')
        assert action.action == ActionType.CLICK
        assert action.target == "#btn"

    @pytest.mark.asyncio
    async def test_parse_response_with_markdown(self):
        from src.vision_engines.gemini_engine import GeminiVisionEngine
        engine = GeminiVisionEngine(api_key="fake-key")
        action = engine._parse_response('```json\n{"thought":"ok","action":"WAIT","confidence":0.5}\n```')
        assert action.action == ActionType.WAIT

    @pytest.mark.asyncio
    async def test_parse_response_invalid_json(self):
        from src.vision_engines.gemini_engine import GeminiVisionEngine
        engine = GeminiVisionEngine(api_key="fake-key")
        action = engine._parse_response("This is not json")
        assert action.action == ActionType.ERROR


class TestOpenRouterVisionEngine:
    @pytest.mark.asyncio
    async def test_parse_response_valid_json(self):
        from src.vision_engines.openrouter_engine import OpenRouterVisionEngine
        engine = OpenRouterVisionEngine(api_key="fake-key")
        action = engine._parse_response('{"thought":"ok","action":"NAVIGATE","value":"https://example.com","confidence":0.9}')
        assert action.action == ActionType.NAVIGATE
        assert action.value == "https://example.com"


class TestLocalVisionEngine:
    @pytest.mark.asyncio
    async def test_parse_response_valid_json(self):
        from src.vision_engines.local_engine import LocalVisionEngine
        # Patch the connectivity check
        with patch("src.vision_engines.local_engine.httpx.get") as mock_get:
            mock_get.return_value = MagicMock()
            engine = LocalVisionEngine(base_url="http://localhost:11434")
            action = engine._parse_response('{"thought":"ok","action":"SCROLL","confidence":0.7}')
            assert action.action == ActionType.SCROLL
